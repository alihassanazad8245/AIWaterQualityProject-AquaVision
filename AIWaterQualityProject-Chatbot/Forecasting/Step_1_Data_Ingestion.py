"""
Step_1_DataIngestion.py

Loads, cleans, and resamples water-quality data into a
regular-frequency time series ready for forecasting.

────────────────────────────────────────────────────────────────
PIPELINE ARCHITECTURE — two decoupled scripts, connected by a file
────────────────────────────────────────────────────────────────
Step_2_WQICalculation.py is run FIRST, separately, as its own
process, directly on the raw data:

    python Step_2_WQICalculation.py raw_data.csv wqi_full_dataset.csv

That produces `wqi_full_dataset.csv` — the original data plus
WQI_Calculated, WQI_Category, Microbial_Status, Risk_Score,
Risk_Category, and Water_Quality_Class.

DataIngestion (this file) is pointed at THAT output file as its
`data_path`. It does not import or call WQICalculation itself —
it only expects those six columns to already be present, and folds
them into cleaning/imputation/resampling like any other column.
Risk_Score is numeric (0–6), so it survives resampling and lands in
`ts_df` next to WQI, ready to be forecast.

FIX (this version)
────────────────────────────────────────────────────────────────
Previously this file kept its OWN copy of the WHO standard limits
(`WHO_STANDARDS`) and its OWN WQI formula (`_wqi_row`), separate
from the authoritative ones in Step_2_WQICalculation.py, and the two
had drifted apart (extra parameters, a different formula for
non-pH values, no minimum-parameter guard). It also never computed
Risk_Score/Risk_Category/Microbial_Status/Water_Quality_Class at
all, so no risk signal ever reached the resampled series.

This version removes the duplicate table/formula entirely.
DataIngestion no longer computes WQI or risk on its own — it
consumes the already-computed columns from Step 2's output file
(`integrate_precomputed_risk()`), so there is exactly one place the
WHO standards and risk logic live: Step_2_WQICalculation.py.
────────────────────────────────────────────────────────────────
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class DataIngestion:

    RESOURCE_TYPE_MAP = {
        "ground water": "Groundwater",
        "drinking water": "Drinking Water",
        "surfacewater": "Surface Water",
    }

    PROVINCE_MAP = {"KPK": "Khyber Pakhtunkhwa", "ICT": "Islamabad"}

    def __init__(self, data_path, target_col="WQI", freq="ME", output_dirs=None):
        self.data_path = data_path
        self.target_col = target_col
        self.freq = freq
        self.cap_bound = {}

        self.df: pd.DataFrame = None       # row-level cleaned frame
        self.ts_df: pd.DataFrame = None    # resampled DatetimeIndex frame (numeric only)
        self.ts_categorical_df: pd.DataFrame = None  # resampled category summary (reference only)

        if output_dirs is None:
            output_dirs = {
                "DataIngestion": "./DataIngestion",
                "MissingValues": "./MissingValues",
            }
        self.output_dirs = output_dirs

    def _makedirs(self):
        for d in self.output_dirs.values():
            os.makedirs(d, exist_ok=True)

    # ── Loading the data ────────────────────────────────────────
    def load_data(self):
        self.df = pd.read_csv(self.data_path)
        print(f"Loaded  {self.df.shape[0]:,} rows  ×  {self.df.shape[1]} cols")
        print(f"Columns : {list(self.df.columns)}")
        return self.df

    # ── Parse and sort by sampling date ─────────────────────────
    def parse_and_sort_by_date(self):
        raw = self.df["Sampling Date"]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Bare-year columns (e.g. 2013, 2015 as int/float) must NOT be
            # passed straight into pd.to_datetime(): pandas treats numeric
            # input as nanoseconds-since-epoch by default, silently
            # collapsing every row to 1970-01-01. Detect this case and
            # parse with format="%Y".
            numeric_raw = pd.to_numeric(raw, errors="coerce")
            looks_like_bare_years = (
                pd.api.types.is_numeric_dtype(raw)
                and numeric_raw.notna().mean() > 0.9
                and numeric_raw.dropna().between(1678, 2262).mean() > 0.9
            )

            if looks_like_bare_years:
                parsed = pd.to_datetime(
                    numeric_raw.astype("Int64").astype(str),
                    format="%Y", errors="coerce",
                )
                print("Sampling Date detected as bare years — parsed with format='%Y'.")
            else:
                parsed = pd.to_datetime(raw, errors="coerce")

        self.df["Sampling Date"] = parsed

        bad = self.df["Sampling Date"].isna().sum()
        if bad:
            print(f"Dropping {bad} rows with un-parseable dates.")
            self.df = self.df[self.df["Sampling Date"].notna()].copy()

        if self.df.empty:
            raise ValueError(
                "All rows were dropped during date parsing — 'Sampling Date' "
                "could not be interpreted. Check the column's format."
            )

        self.df.sort_values("Sampling Date", inplace=True)
        self.df.reset_index(drop=True, inplace=True)

        date_min = self.df["Sampling Date"].min()
        date_max = self.df["Sampling Date"].max()
        print(f"Date range: {date_min.date()}  to {date_max.date()}")

        if date_min.year == date_max.year == 1970:
            raise ValueError(
                "Parsed dates collapsed to the 1970 epoch — this usually means "
                "'Sampling Date' was numeric and misread as nanosecond "
                "timestamps. Check the source column's format."
            )

        return self.df

    # ── Dropping irrelevant columns ─────────────────────────────
    def drop_irrelevant_columns(self):
        drop_cols = ["Reference", "Sample_ID", "Country"]
        existing = [c for c in drop_cols if c in self.df.columns]
        if existing:
            self.df.drop(columns=existing, inplace=True)
            print(f"Dropped ID columns: {existing}")
        return self.df

    # ── Removing duplicate values ────────────────────────────────
    def remove_duplicates(self):
        before = len(self.df)
        self.df.drop_duplicates(inplace=True)
        removed = before - len(self.df)
        if removed:
            print(f"Removed {removed} duplicate rows.")
        return self.df

    # ── Mapping categorical values ──────────────────────────────
    def map_categorical(self):
        if "Resource Type" in self.df.columns:
            self.df["Resource Type"] = (
                self.df["Resource Type"].str.strip().str.lower()
                .map(lambda x: self.RESOURCE_TYPE_MAP.get(x, x.title()) if pd.notna(x) else x)
            )
        if "Province" in self.df.columns:
            self.df["Province"] = (
                self.df["Province"].str.strip()
                .map(lambda x: self.PROVINCE_MAP.get(x, x) if pd.notna(x) else x)
            )
        return self.df

    # ── Coerce numeric strings ──────────────────────────────────
    def coerce_numeric_strings(self):
        skip = {
            "Sampling Date", "Resource Type", "Province", "City", "District/Area",
            "Water Quality Class",
            # Categorical columns produced by the WQI/Risk pipeline
            # (WQICalculation, called from run_risk_assessment()) —
            # these must never be coerced to numeric or they collapse to NaN.
            "WQI_Category", "Microbial_Status", "Risk_Category", "Water_Quality_Class",
        }
        for col in self.df.columns:
            if col in skip:
                continue
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                before_non_null = self.df[col].notna().sum()
                self.df[col] = (
                    self.df[col].astype(str).str.replace(",", "", regex=False)
                    .str.strip().str.lower()
                    .str.replace(r"^bdl?$", "0", regex=True)
                    .str.replace(r"^bl$", "0", regex=True)
                )
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                after_non_null = self.df[col].notna().sum()
                if before_non_null > 0 and after_non_null == 0:
                    print(f"[WARN] Column '{col}' became entirely NaN after "
                          f"numeric coercion ({before_non_null} non-null values "
                          f"lost). It was likely text and should be added to "
                          f"the 'skip' set in coerce_numeric_strings().")
        return self.df

    # ── Fixing Arsenic unit ─────────────────────────────────────
    def fix_arsenic_unit(self):
        col = "Arsenic (mg/L)"
        if col in self.df.columns:
            mask = self.df[col].notna() & (self.df[col] > 1)
            if mask.sum():
                self.df.loc[mask, col] /= 1000.0
                print(f"Arsenic: {mask.sum()} rows converted µg/L → mg/L")
        return self.df

    # ── Missing values treatment (ffill / bfill) ────────────────
    def impute_missing_values(self):
        before_total = self.df.isna().sum().sum()

        plt.figure(figsize=(12, 6))
        self.df.isnull().sum().sort_values(ascending=False).plot(kind="bar", color="salmon")
        plt.title("Missing Values BEFORE Treatment", fontsize=13)
        plt.ylabel("Count"); plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dirs["MissingValues"], "missing_before.png"))
        plt.close()

        self.df.isnull().sum().to_csv(os.path.join(self.output_dirs["MissingValues"], "missing_count_before.csv"))

        numeric_cols = self.df.select_dtypes(include=np.number).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != self.target_col]
        cat_cols = ["Resource Type", "Province", "City", "District/Area",
                    "Water Quality Class",
                    "WQI_Category", "Microbial_Status", "Risk_Category", "Water_Quality_Class"]
        cat_cols = [c for c in cat_cols if c in self.df.columns]

        for col in numeric_cols + cat_cols:
            self.df[col] = self.df[col].ffill().bfill()

        after_total = self.df.isna().sum().sum()
        print(f"Missing values: {before_total} to {after_total} "
              f"(ffill + bfill applied)")

        plt.figure(figsize=(12, 6))
        self.df.isnull().sum().sort_values(ascending=False).plot(kind="bar", color="steelblue")
        plt.title("Missing Values AFTER Treatment (ffill → bfill)", fontsize=13)
        plt.ylabel("Count"); plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dirs["MissingValues"], "missing_after.png"))
        plt.close()

        return self.df

    # ── Capping outliers using IQR method ───────────────────────
    def cap_outliers(self):
        """
        Caps raw numeric measurement columns using IQR bounds.

        Runs BEFORE run_risk_assessment() intentionally: chemical
        readings should be cleaned first, then WQI / Risk_Score are
        derived from the cleaned values. Risk_Score itself is
        therefore never distorted by this step (it doesn't exist
        yet when this runs).
        """
        num_cols = self.df.select_dtypes(include=np.number).columns.tolist()
        for col in num_cols:
            Q1, Q3 = self.df[col].quantile(0.25), self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lb = Q1 - 1.5 * IQR
            ub = Q3 + 1.5 * IQR
            self.cap_bound[col] = (lb, ub)
            self.df[col] = self.df[col].clip(lb, ub)
        return self.df

    # ── Integrate precomputed risk columns (from Step 2's output file) ──
    def integrate_precomputed_risk(self):
        """
        DataIngestion does NOT compute WQI or risk itself. It expects
        `data_path` to already be Step 2's output — the file produced
        by running Step_2_WQICalculation.py separately on the raw
        data — which contains:

            WQI_Calculated, WQI_Category, Microbial_Status,
            Risk_Score, Risk_Category, Water_Quality_Class

        This method just checks those columns are present, fills the
        forecasting target_col (default 'WQI') from WQI_Calculated
        wherever it was missing, and mirrors Water_Quality_Class into
        a 'Water Quality Class' column for backward compatibility
        with anything downstream expecting that exact name.

        If the precomputed columns are missing, this warns rather
        than failing outright — the WQI/date/cleaning parts of the
        pipeline can still run, but Risk_Score will not be available
        for forecasting until Step 2 has been run on this file.
        """
        precomputed_cols = [
            "WQI_Calculated", "WQI_Category", "Microbial_Status",
            "Risk_Score", "Risk_Category", "Water_Quality_Class",
        ]
        present = [c for c in precomputed_cols if c in self.df.columns]
        missing = [c for c in precomputed_cols if c not in self.df.columns]

        if missing:
            print(f"[WARN] Precomputed risk columns not found in input file: {missing}.")
            print(f"       Run Step_2_WQICalculation.py on the raw data first, e.g.:")
            print(f"           python Step_2_WQICalculation.py raw_data.csv wqi_full_dataset.csv")
            print(f"       then point DataIngestion at 'wqi_full_dataset.csv' instead.")
        else:
            print(f"\nFound precomputed risk columns from Step 2: {present}")

        # ── Fill target_col from WQI_Calculated wherever available ──
        if self.target_col not in self.df.columns:
            self.df[self.target_col] = np.nan

        if "WQI_Calculated" in self.df.columns:
            missing_mask = self.df[self.target_col].isna()
            filled = missing_mask.sum()
            if filled:
                self.df.loc[missing_mask, self.target_col] = self.df.loc[missing_mask, "WQI_Calculated"]

            cap_99 = self.df[self.target_col].quantile(0.99)
            self.df[self.target_col] = self.df[self.target_col].clip(upper=cap_99)
            self.df[self.target_col] = self.df[self.target_col].ffill().bfill()

            print(f"Target column '{self.target_col}' filled for {filled} rows | "
                  f"mean={self.df[self.target_col].mean():.2f}  "
                  f"std={self.df[self.target_col].std():.2f}  "
                  f"max={self.df[self.target_col].max():.2f}")

        if "Risk_Score" in self.df.columns:
            print(f"Risk_Score present as a numeric column "
                  f"(mean={self.df['Risk_Score'].mean():.2f}) and will flow "
                  f"into the resampled time series for forecasting.")

        if "Water_Quality_Class" in self.df.columns:
            self.df["Water Quality Class"] = self.df["Water_Quality_Class"]

        return self.df

    # ── Resampling ───────────────────────────────────────────────
    def resample_to_regular_frequency(self) -> pd.DataFrame:
        self.df.set_index("Sampling Date", inplace=True)
        self.df.index.name = "Date"

        # Numeric columns now include Risk_Score (0–6) alongside WQI,
        # so risk trend flows into the forecasting series automatically.
        num_cols = self.df.select_dtypes(include=np.number).columns.tolist()
        self.ts_df = (self.df[num_cols].resample(self.freq).mean())
        self.ts_df = self.ts_df.ffill().bfill()

        n_gaps = self.ts_df[self.target_col].isna().sum()
        if n_gaps:
            print(f"[WARN] {n_gaps} WQI periods still NaN after ffill/bfill.")

        # ── Reference-only categorical summary (mode per period) ──
        # Risk_Category / Microbial_Status / Water_Quality_Class can't
        # be averaged, but a per-period "most common" label is useful
        # context alongside the numeric Risk_Score trend. Not required
        # for forecasting — kept separate from ts_df on purpose.
        cat_cols = [c for c in ["Risk_Category", "Microbial_Status", "Water_Quality_Class"]
                    if c in self.df.columns]
        if cat_cols:
            self.ts_categorical_df = (
                self.df[cat_cols]
                .resample(self.freq)
                .agg(lambda s: s.mode().iat[0] if not s.mode().empty else np.nan)
            )

        print(f"Resampled  freq='{self.freq}' to {len(self.ts_df)} periods  "
              f"[{self.ts_df.index[0].date()} to {self.ts_df.index[-1].date()}]")

        if len(self.ts_df) < 2:
            raise ValueError(
                f"Resampling at freq='{self.freq}' produced only "
                f"{len(self.ts_df)} period(s) — too little data for a train/test "
                f"split or modeling. This usually means the source date range is "
                f"too narrow, or the frequency is too coarse relative to the raw "
                f"dates. Try a finer freq (e.g. 'D' or 'W') or check date parsing."
            )
        if self.ts_df[self.target_col].nunique() <= 1:
            print(f"[WARN] '{self.target_col}' is constant after resampling — "
                  f"stationarity tests and most models will be degenerate. "
                  f"This typically means the raw data is too sparse for freq="
                  f"'{self.freq}' and forward/back-fill is masking large gaps.")

        return self.ts_df

    # ── Save artefacts ───────────────────────────────────────────
    def _save_artifacts(self):
        self.ts_df.to_csv(os.path.join(self.output_dirs["DataIngestion"], "ts_resampled.csv"))
        self.df.to_csv(os.path.join(self.output_dirs["DataIngestion"], "df_cleaned.csv"))

        if self.ts_categorical_df is not None:
            self.ts_categorical_df.to_csv(
                os.path.join(self.output_dirs["DataIngestion"], "ts_categorical_summary.csv")
            )

        # WQI time-series quick-look plot
        plt.figure(figsize=(14, 4))
        plt.plot(self.ts_df.index, self.ts_df[self.target_col], color="steelblue", linewidth=1.5)
        plt.title(f"WQI Time Series after Ingestion  (freq='{self.freq}')", fontsize=13)
        plt.xlabel("Date"); plt.ylabel("WQI")
        plt.grid(alpha=0.3); plt.tight_layout()
        plt.savefig(os.path.join(self.output_dirs["DataIngestion"], "wqi_after_ingestion.png"))
        plt.close()

        # Risk_Score time-series quick-look plot (new — was absent before)
        if "Risk_Score" in self.ts_df.columns:
            plt.figure(figsize=(14, 4))
            plt.plot(self.ts_df.index, self.ts_df["Risk_Score"], color="firebrick", linewidth=1.5)
            plt.title(f"Risk Score Time Series after Ingestion  (freq='{self.freq}')", fontsize=13)
            plt.xlabel("Date"); plt.ylabel("Risk_Score (0–6)")
            plt.grid(alpha=0.3); plt.tight_layout()
            plt.savefig(os.path.join(self.output_dirs["DataIngestion"], "risk_score_after_ingestion.png"))
            plt.close()

        print("Artefacts saved.")

    def run_pipeline(self) -> pd.DataFrame:
        self._makedirs()
        self.load_data()
        self.parse_and_sort_by_date()
        self.drop_irrelevant_columns()
        self.remove_duplicates()
        self.map_categorical()
        self.coerce_numeric_strings()
        self.fix_arsenic_unit()
        self.impute_missing_values()
        self.cap_outliers()
        self.integrate_precomputed_risk()   # consumes Step 2's output columns
        self.resample_to_regular_frequency()
        self._save_artifacts()
        print("\n Data Ingestion completed successfully.\n")
        return self.ts_df