"""
Step_1_Data_Preparation.py

Loads the already-computed dataset (e.g. merge.csv, the output of
Step_2_WQICalculation.py + Step_1_DataIngestion.py from the earlier
pipeline) and prepares it for regression modeling — WITHOUT needing
the caller to manually specify a target column or feature list.

────────────────────────────────────────────────────────────────
WHY AUTO-DETECTION
────────────────────────────────────────────────────────────────
merge.csv already contains every calculated outcome:

    WQI, Water Quality Class,
    WQI_Calculated, WQI_Category,
    Microbial_Status, Risk_Score, Risk_Category,
    Water_Quality_Class

main.py instantiates this class with no target_col:

    preparation = DataPreparation(data_path="merge.csv", output_dirs=output_dirs)

So this class must pick a sensible target on its own. It does that
via TARGET_PRIORITY — the first of these columns found in the file
becomes the regression target unless the caller overrides it. Right
now that means WQI_Calculated (per your instruction), but a caller
can still pass target_col="Risk_Score" explicitly to switch targets
without touching this file.

────────────────────────────────────────────────────────────────
WHY THE OUTCOME COLUMNS ARE DROPPED FROM FEATURES
────────────────────────────────────────────────────────────────
All 8 outcome columns are derived from the SAME chemical readings
(and, for Risk_Score/Microbial_Status, from E. Coli/Total Coliform
as well). If WQI_Calculated is the target, leaving WQI, WQI_Category,
or Water_Quality_Class in as a feature would let the model "read the
answer off" a near-duplicate column instead of learning from the
raw chemistry — this is target leakage, not real predictive signal.
So: target_col stays in df_model_ready as the label, and every OTHER
outcome column is dropped before modeling, regardless of which one
was chosen as the target.

────────────────────────────────────────────────────────────────
INTERFACE (what downstream Step_2..Step_10 files expect)
────────────────────────────────────────────────────────────────
    preparation = DataPreparation(data_path="merge.csv", output_dirs=output_dirs)
    preparation.run_pipeline()

    preparation.df             -> cleaned frame, outcome columns intact
                                   (City/Province/target all present —
                                   used by EDA for per-city baselines)
    preparation.df_model_ready -> numeric, one-hot encoded, leakage-free
                                   frame INCLUDING the target column
                                   (used by DataTransform / FeatureSelection
                                   / DataSplitter)
    preparation.target_col     -> the auto-detected (or overridden) target
                                   column name, e.g. "WQI_Calculated"
────────────────────────────────────────────────────────────────
"""

import os
import numpy as np
import pandas as pd


class DataPreparation:

    # First match found in the file wins, unless target_col is passed
    # explicitly to __init__. WQI_Calculated is listed first per current
    # instruction to regress chemical water quality.
    TARGET_PRIORITY = [
        "WQI_Calculated",
        "WQI",
        "Risk_Score",
    ]

    # Every column that is itself an outcome of the WQI/Risk pipeline —
    # near-duplicates or re-labelings of each other. Whichever one is
    # the target, all the rest are leakage and must not be features.
    OUTCOME_COLUMNS = [
        "WQI",
        "Water Quality Class",
        "WQI_Calculated",
        "WQI_Category",
        "Microbial_Status",
        "Risk_Score",
        "Risk_Category",
        "Water_Quality_Class",
    ]

    CATEGORICAL_COLUMNS = ["Province", "City", "Resource Type"]

    DATE_COLUMN = "Sampling Date"

    def __init__(self, data_path, target_col=None, output_dirs=None):
        self.data_path = data_path
        self.target_col = target_col          # None → auto-detect in run_pipeline()
        self.output_dirs = output_dirs or {}

        self.df: pd.DataFrame = None            # cleaned, outcome columns intact
        self.df_model_ready: pd.DataFrame = None  # numeric, encoded, leakage-free + target

        self.leakage_dropped = []
        self.categoricals_encoded = []

    def _makedirs(self):
        for d in self.output_dirs.values():
            os.makedirs(d, exist_ok=True)

    # ── Load ─────────────────────────────────────────────────────
    def load_data(self):
        self.df = pd.read_csv(self.data_path)
        print(f"Loaded {self.df.shape[0]:,} rows x {self.df.shape[1]} cols from {self.data_path}")
        return self.df

    # ── Auto-detect target ──────────────────────────────────────
    def detect_target(self):
        """
        Picks the regression target automatically if the caller
        didn't specify one. Priority order defined in
        TARGET_PRIORITY — first match present in the loaded file
        wins.
        """
        if self.target_col is not None:
            if self.target_col not in self.df.columns:
                raise ValueError(
                    f"target_col='{self.target_col}' was specified but is not "
                    f"a column in {self.data_path}. Available outcome columns: "
                    f"{[c for c in self.OUTCOME_COLUMNS if c in self.df.columns]}"
                )
            print(f"Target column (explicit): '{self.target_col}'")
            return self.target_col

        for candidate in self.TARGET_PRIORITY:
            if candidate in self.df.columns:
                self.target_col = candidate
                print(f"Target column (auto-detected): '{self.target_col}'")
                return self.target_col

        raise ValueError(
            f"Could not auto-detect a target column — none of "
            f"{self.TARGET_PRIORITY} were found in {self.data_path}. "
            f"Pass target_col explicitly to DataPreparation(...)."
        )

    # ── Validate target ──────────────────────────────────────────
    def validate_target(self):
        self.df[self.target_col] = pd.to_numeric(self.df[self.target_col], errors="coerce")
        before = len(self.df)
        self.df = self.df[self.df[self.target_col].notna()].copy()
        dropped = before - len(self.df)
        if dropped:
            print(f"Dropped {dropped} rows with missing/unparseable target '{self.target_col}'")
        return self.df

    # ── Date feature engineering ────────────────────────────────
    def engineer_date_features(self):
        if self.DATE_COLUMN in self.df.columns:
            self.df[self.DATE_COLUMN] = pd.to_datetime(self.df[self.DATE_COLUMN], errors="coerce")
            self.df["Sampling_Year"] = self.df[self.DATE_COLUMN].dt.year
            self.df["Sampling_Month"] = self.df[self.DATE_COLUMN].dt.month
            print("Engineered 'Sampling_Year' / 'Sampling_Month' from Sampling Date")
        return self.df

    # ── Missing value handling (light touch — a SimpleImputer runs ─
    #    again downstream in main.py, so this just avoids obviously
    #    broken rows/columns going into feature selection/EDA) ─────
    def handle_missing_values(self):
        num_cols = self.df.select_dtypes(include=np.number).columns.tolist()
        num_cols = [c for c in num_cols if c != self.target_col]
        for col in num_cols:
            if self.df[col].isna().any():
                self.df[col] = self.df[col].fillna(self.df[col].median())

        cat_cols = [c for c in self.CATEGORICAL_COLUMNS if c in self.df.columns]
        for col in cat_cols:
            if self.df[col].isna().any():
                mode = self.df[col].mode()
                self.df[col] = self.df[col].fillna(mode.iat[0] if not mode.empty else "Unknown")

        return self.df

    # ── Build model-ready frame ─────────────────────────────────
    def build_model_ready_frame(self):
        """
        Produces df_model_ready:
          - starts from the cleaned self.df
          - drops every OUTCOME_COLUMNS entry EXCEPT the chosen target
            (leakage removal — see module docstring)
          - drops the raw date column (already engineered into
            Sampling_Year / Sampling_Month above)
          - one-hot encodes Province / City / Resource Type
          - target column is kept, numeric, at the end
        """
        leakage = [c for c in self.OUTCOME_COLUMNS if c in self.df.columns and c != self.target_col]
        self.leakage_dropped = leakage

        model_df = self.df.drop(columns=leakage, errors="ignore")

        if self.DATE_COLUMN in model_df.columns:
            model_df = model_df.drop(columns=[self.DATE_COLUMN])

        cat_cols = [c for c in self.CATEGORICAL_COLUMNS if c in model_df.columns]
        if cat_cols:
            model_df = pd.get_dummies(model_df, columns=cat_cols, drop_first=True)
            # pandas returns dummy columns as bool dtype, which
            # select_dtypes(include=np.number) does NOT count as numeric —
            # cast to int now so they survive the numeric check below and
            # aren't mistaken for leftover unencoded text columns.
            dummy_cols = model_df.select_dtypes(include="bool").columns
            model_df[dummy_cols] = model_df[dummy_cols].astype(int)
            self.categoricals_encoded = cat_cols

        # Anything still non-numeric at this point wasn't accounted for —
        # coerce or drop it rather than silently feeding strings to models.
        remaining_object_cols = model_df.select_dtypes(exclude=np.number).columns.tolist()
        remaining_object_cols = [c for c in remaining_object_cols if c != self.target_col]
        if remaining_object_cols:
            print(f"[WARN] Non-numeric columns not handled by encoding, dropping: {remaining_object_cols}")
            model_df = model_df.drop(columns=remaining_object_cols)

        self.df_model_ready = model_df

        print(f"\nLeakage columns dropped from features: {leakage}")
        print(f"Categorical columns one-hot encoded: {self.categoricals_encoded}")
        print(f"df_model_ready shape: {self.df_model_ready.shape}")
        print(f"df_model_ready columns: {list(self.df_model_ready.columns)}")

        return self.df_model_ready

    # ── Save artefacts ───────────────────────────────────────────
    def _save_artifacts(self):
        out_dir = self.output_dirs.get("Datapreparation", ".")
        os.makedirs(out_dir, exist_ok=True)
        self.df.to_csv(os.path.join(out_dir, "df_cleaned.csv"), index=False)
        self.df_model_ready.to_csv(os.path.join(out_dir, "df_model_ready.csv"), index=False)
        print(f"Saved: {out_dir}/df_cleaned.csv, {out_dir}/df_model_ready.csv")

    # ── Full pipeline ────────────────────────────────────────────
    def run_pipeline(self):
        print("\n" + "=" * 55)
        print("     STEP 1: DATA PREPARATION")
        print("=" * 55)

        self._makedirs()
        self.load_data()
        self.detect_target()
        self.validate_target()
        self.engineer_date_features()
        self.handle_missing_values()
        self.build_model_ready_frame()
        self._save_artifacts()

        print("\nData Preparation completed successfully.")
        print(f"Target: '{self.target_col}'  |  "
              f"df: {self.df.shape}  |  df_model_ready: {self.df_model_ready.shape}")

        return self.df, self.df_model_ready