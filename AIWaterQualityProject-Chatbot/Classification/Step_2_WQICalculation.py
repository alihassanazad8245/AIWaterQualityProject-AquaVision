"""
Step_2_WQICalculation.py

Calculates Water Quality Index (WQI) using WHO standard
formula and assigns water quality categories.

WHO WQI Formula:
    Step 1: Unit Weight (Wi) = 1 / Si
            Si = WHO standard limit for parameter i

    Step 2: Quality Rating (qi) = (Ci - ideal) / (Si - ideal) * 100
            Ci = actual measured value
            ideal = 7.0 for pH, 0.0 for all others

    Step 3: WQI = sum(Wi * qi) / sum(Wi)

WQI Categories (Heliyon 2023, doi:10.1016/j.heliyon.2023.e13872):
    0  – 50  : Excellent
    51 – 100 : Good
    101 – 200: Poor
    201 – 300: Very Poor
    > 300    : Unsuitable for drinking

Microbial Assessment:
    E. coli > 0 OR Total Coliform > 0 → Contaminated
    Otherwise                          → Safe

Risk Assessment (Heliyon 2023, Table 1–2):
    Score 0 → Marginally Safe
    Score 1 → Low  (microbial only)
    Score 2 → Low  (TDS only)
    Score 3 → Medium (single chemical)
    Score 4 → Medium (single chemical + microbial)
    Score 5 → High  (two or more chemical contaminants)
    Score 6 → High  (multiple chemical + microbial)

Water_Quality_Class (composite — all five signals):
    Each of the five assessment dimensions contributes a
    penalty level (0–4). The final class is the WORST
    (maximum) penalty across all dimensions, ensuring no
    hazard is masked by good scores elsewhere.

    Penalty → Class mapping:
        0 → Excellent
        1 → Good
        2 → Poor
        3 → Very Poor
        4 → Unsuitable

Reference:
    WHO Guidelines for Drinking Water Quality (4th Ed.)
    Heliyon 2023 — https://doi.org/10.1016/j.heliyon.2023.e13872
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


class WQICalculation:
    """
    Calculates WQI score, assigns water quality category,
    assesses microbial status, and computes risk score/category
    for each water sample using WHO / NEQS guidelines.

    Attributes:
        df          (DataFrame) : Input prepared dataframe
        output_dir  (str)       : Path to save WQI results
    """

    # ── WHO Standard Limits (Si) ──────────────────────────────────
    WHO_LIMITS = {
        # ── Core Drinking Water Parameters ─────────────────────
        'pH': 8.5,                    # upper acceptable limit (range: 6.5–8.5)
        'Turbidity (NTU)': 5.0,
        'TDS (mg/L)': 1000.0,

        # ── Major Ions ─────────────────────────────────────────
        'Chloride (mg/L)': 250.0,
        'Sulfate (mg/L)': 250.0,
        'Nitrate (mg/L)': 50.0,
        'Fluoride (mg/L)': 1.5,

        # ── Heavy Metals (CRITICAL for health risk) ────────────
        'Arsenic (mg/L)': 0.01,
        'Iron (mg/L)': 0.3,
        'Lead (mg/L)': 0.01,
        'Cadmium (mg/L)': 0.003,
        'Chromium (mg/L)': 0.05,
        'Mercury (mg/L)': 0.006,
    }

    # ── Ideal Values (Ci_ideal) ───────────────────────────────────
    IDEAL_VALUES = {
        'pH': 7.0,
        'Turbidity (NTU)': 0.0,
        'TDS (mg/L)': 0.0,
        'Chloride (mg/L)': 0.0,
        'Sulfate (mg/L)': 0.0,
        'Nitrate (mg/L)': 0.0,
        'Fluoride (mg/L)': 0.0,
        'Arsenic (mg/L)': 0.0,
        'Iron (mg/L)': 0.0,
        'Lead (mg/L)': 0.0,
        'Cadmium (mg/L)': 0.0,
        'Chromium (mg/L)': 0.0,
        'Mercury (mg/L)': 0.0,
    }

    # ── WQI Categories (Heliyon 2023 / WHO) ──────────────────────
    WQI_CATEGORIES = [
        (0,   50,            'Excellent'),
        (50,  100,           'Good'),
        (100, 200,           'Poor'),
        (200, 300,           'Very Poor'),
        (300, float('inf'), 'Unsuitable for drinking'),
    ]

    # ── Chemical parameters considered for risk scoring ───────────
    RISK_CHEMICAL_PARAMS = [
        'Arsenic (mg/L)',
        'Fluoride (mg/L)',
        'Nitrate (mg/L)',
        'Lead (mg/L)',
        'Cadmium (mg/L)',
        'Chromium (mg/L)',
        'Mercury (mg/L)',
    ]

    # ── Penalty tables used by assign_water_quality_class ─────────
    # Each dimension maps its possible values to a penalty level
    # (0 = best, 4 = worst). The composite class is determined by
    # the maximum penalty across all five dimensions so that a
    # single serious hazard cannot be hidden by clean scores.

    _WQI_CATEGORY_PENALTY = {
        'Excellent':              0,
        'Good':                   1,
        'Poor':                   2,
        'Very Poor':              3,
        'Unsuitable for drinking': 4,
    }

    _MICROBIAL_PENALTY = {
        'Safe':          0,
        'Contaminated':  3,   # microbial contamination is a serious hazard
    }

    _RISK_SCORE_PENALTY = {
        0: 0,   # Marginally Safe
        1: 1,   # Microbial only  → Low
        2: 1,   # TDS only        → Low
        3: 2,   # Single chemical → Medium
        4: 3,   # Chemical + microbial → Medium-High
        5: 3,   # Multiple chemical   → High
        6: 4,   # Multiple chemical + microbial → Highest
    }

    _RISK_CATEGORY_PENALTY = {
        'Marginally Safe': 0,
        'Low':             1,
        'Medium':          2,
        'High':            3,
    }

    _PENALTY_TO_CLASS = {
        0: 'Excellent',
        1: 'Good',
        2: 'Poor',
        3: 'Very Poor',
        4: 'Unsuitable',
    }

    # ─────────────────────────────────────────────────────────────
    def __init__(self, df: pd.DataFrame, output_dir: str = './WQIResults'):
        """
        Initialize WQICalculation.

        Args:
            df         : Prepared DataFrame from Step 1
            output_dir : Folder to save WQI results & plots
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if df.empty:
            raise ValueError("Input DataFrame is empty")

        self.df = df.copy()

        # Ensure numeric conversion for all WHO parameters
        for col in self.WHO_LIMITS.keys():
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # Also coerce microbial columns if present
        for col in ['E. Coli', 'Total Coliform']:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        self.output_dir = output_dir

        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            raise OSError(f"Failed to create output directory: {e}")

        print("\nWQI Module Initialized")
        print(f"Dataset shape : {self.df.shape}")

        available_params = [col for col in self.WHO_LIMITS.keys() if col in self.df.columns]
        print(f"Parameters found: {len(available_params)}")

        missing_params = set(self.WHO_LIMITS.keys()) - set(available_params)
        if missing_params:
            print(f"Missing parameters: {len(missing_params)} (will be skipped)")

    # ─────────────────────────────────────────────────────────────
    def _calculate_wqi_for_row(self, row: pd.Series) -> float:
        """
        Calculate WQI for a single sample row using the
        WHO-based weighted arithmetic method.

        E. coli and Total Coliform are intentionally excluded from
        WQI calculation (Si = 0 CFU/100 mL makes the formula
        inapplicable; microbial status is assessed separately).

        Returns:
            WQI score (float) or NaN if insufficient data
        """

        total_weight = 0.0
        weighted_qi_sum = 0.0
        params_used = 0

        for param, Si in self.WHO_LIMITS.items():

            if param not in row.index:
                continue

            Ci = row[param]
            ideal = self.IDEAL_VALUES.get(param, 0.0)

            if pd.isna(Ci) or Si == 0:
                continue

            try:
                Ci = float(Ci)
            except (ValueError, TypeError):
                continue

            # ── Unit Weight ───────────────────────────────
            Wi = 1.0 / Si

            # ── Quality Rating (qi) ───────────────────────
            denominator = abs(Si - ideal)
            if denominator == 0:
                continue

            qi = (abs(Ci - ideal) / denominator) * 100

            weighted_qi_sum += Wi * qi
            total_weight += Wi
            params_used += 1

        if params_used < 5 or total_weight == 0:
            return np.nan

        wqi = weighted_qi_sum / total_weight

        return round(wqi, 4)

    # ─────────────────────────────────────────────────────────────
    def calculate_wqi(self) -> pd.DataFrame:
        """
        Calculate WQI for all rows in the dataset.

        Returns:
            DataFrame with WQI_Calculated column added
        """
        print("\nCalculating WQI for all samples...")

        available_params = [p for p in self.WHO_LIMITS.keys() if p in self.df.columns]

        print(f"Parameters used ({len(available_params)}):")
        for p in available_params:
            print(f"  → {p} (WHO limit: {self.WHO_LIMITS[p]})")

        self.df['WQI_Calculated'] = self.df.apply(
            self._calculate_wqi_for_row, axis=1
        )

        calculated = self.df['WQI_Calculated'].notna().sum()
        print(f"\nWQI calculated for {calculated} samples")

        if calculated > 0:
            print(f"   Min  : {self.df['WQI_Calculated'].min():.2f}")
            print(f"   Max  : {self.df['WQI_Calculated'].max():.2f}")
            print(f"   Mean : {self.df['WQI_Calculated'].mean():.2f}")
            print(f"   Std  : {self.df['WQI_Calculated'].std():.2f}")
        else:
            print("   No valid WQI values calculated.")

        return self.df

    # ─────────────────────────────────────────────────────────────
    def assign_category(self) -> pd.DataFrame:
        """
        Assign WQI water quality category based solely on
        the calculated WQI value (no WHO safety overrides).

        Categories (Heliyon 2023 / WHO):
            0  – 50  → Excellent
            51 – 100 → Good
            101 – 200→ Poor
            201 – 300→ Very Poor
            > 300    → Unsuitable for drinking
        """

        def get_category(wqi):
            if pd.isna(wqi):
                return np.nan
            if wqi <= 50:
                return 'Excellent'
            elif wqi <= 100:
                return 'Good'
            elif wqi <= 200:
                return 'Poor'
            elif wqi <= 300:
                return 'Very Poor'
            else:
                return 'Unsuitable for drinking'

        self.df['WQI_Category'] = self.df['WQI_Calculated'].apply(get_category)

        print("\nWater Quality Categories Assigned:")
        print(
            self.df['WQI_Category']
            .value_counts(dropna=False)
            .to_string()
        )

        return self.df

    # ─────────────────────────────────────────────────────────────
    def assign_microbial_status(self) -> pd.DataFrame:
        """
        Assign Microbial_Status based on E. Coli and Total Coliform.

        Rules:
            E. Coli > 0          → 'Contaminated'
            Total Coliform > 0   → 'Contaminated'
            Otherwise            → 'Safe'

        Stores result in self.df['Microbial_Status'].
        """

        def get_microbial_status(row):
            try:
                ecoli = row.get('E. Coli', np.nan)
                if pd.notna(ecoli) and float(ecoli) > 0:
                    return 'Contaminated'
            except (ValueError, TypeError):
                pass

            try:
                tc = row.get('Total Coliform', np.nan)
                if pd.notna(tc) and float(tc) > 0:
                    return 'Contaminated'
            except (ValueError, TypeError):
                pass

            return 'Safe'

        self.df['Microbial_Status'] = self.df.apply(get_microbial_status, axis=1)

        print("\nMicrobial Status Assigned:")
        print(
            self.df['Microbial_Status']
            .value_counts(dropna=False)
            .to_string()
        )

        return self.df

    # ─────────────────────────────────────────────────────────────
    def calculate_risk_score(self) -> pd.DataFrame:
        """
        Calculate Risk_Score for each sample based on the
        presence of chemical and microbial contaminants.

        Risk Score Mapping (Heliyon 2023, Table 1):
            0 → No contamination (all within limits)
            1 → Microbial contamination only
            2 → TDS only exceeds limit
            3 → Single chemical contaminant exceeds limit
            4 → Single chemical + microbial contamination
            5 → Two or more chemical contaminants exceed limits
            6 → Multiple chemical + microbial contamination

        Chemical parameters evaluated:
            Arsenic, Fluoride, Nitrate, Lead,
            Cadmium, Chromium, Mercury

        Stores result in self.df['Risk_Score'].
        """

        def get_risk_score(row):
            # ── Count chemical exceedances ──────────────
            chem_exceedances = 0
            for param in self.RISK_CHEMICAL_PARAMS:
                limit = self.WHO_LIMITS.get(param)
                if limit is None or param not in row.index:
                    continue
                try:
                    val = float(row[param])
                    if not np.isnan(val) and val > limit:
                        chem_exceedances += 1
                except (ValueError, TypeError):
                    pass

            # ── TDS exceedance ──────────────────────────
            tds_exceeded = False
            try:
                tds_val = float(row.get('TDS (mg/L)', np.nan))
                if not np.isnan(tds_val) and tds_val > self.WHO_LIMITS['TDS (mg/L)']:
                    tds_exceeded = True
            except (ValueError, TypeError):
                pass

            # ── Microbial contamination ─────────────────
            microbial = row.get('Microbial_Status', 'Safe') == 'Contaminated'

            # ── Risk Score Logic ────────────────────────
            if chem_exceedances == 0 and not tds_exceeded and not microbial:
                return 0   # Marginally Safe

            if microbial and chem_exceedances == 0 and not tds_exceeded:
                return 1   # Microbial only → Low

            if tds_exceeded and chem_exceedances == 0 and not microbial:
                return 2   # TDS only → Low

            if chem_exceedances == 1 and not microbial:
                return 3   # Single chemical → Medium

            if chem_exceedances == 1 and microbial:
                return 4   # Single chemical + microbial → Medium

            if chem_exceedances >= 2 and not microbial:
                return 5   # Multiple chemical → High

            if chem_exceedances >= 2 and microbial:
                return 6   # Multiple chemical + microbial → High

            # Fallback: TDS + microbial with no chemical exceedances
            if tds_exceeded and microbial:
                return 4

            return 0

        self.df['Risk_Score'] = self.df.apply(get_risk_score, axis=1)

        print("\nRisk Scores Calculated:")
        print(
            self.df['Risk_Score']
            .value_counts(dropna=False)
            .sort_index()
            .to_string()
        )

        return self.df

    # ─────────────────────────────────────────────────────────────
    def assign_risk_category(self) -> pd.DataFrame:
        """
        Assign Risk_Category based on Risk_Score.

        Mapping (Heliyon 2023, Table 2):
            0       → Marginally Safe
            1, 2    → Low
            3, 4    → Medium
            5, 6    → High
        """

        def get_risk_category(score):
            if pd.isna(score):
                return np.nan
            score = int(score)
            if score == 0:
                return 'Marginally Safe'
            elif score in (1, 2):
                return 'Low'
            elif score in (3, 4):
                return 'Medium'
            else:
                return 'High'

        self.df['Risk_Category'] = self.df['Risk_Score'].apply(get_risk_category)

        print("\nRisk Categories Assigned:")
        print(
            self.df['Risk_Category']
            .value_counts(dropna=False)
            .to_string()
        )

        return self.df

    # ─────────────────────────────────────────────────────────────
    def assign_water_quality_class(self) -> pd.DataFrame:
        """
        Assign a composite Water_Quality_Class that integrates
        all five assessment dimensions:

            1. WQI_Calculated  — chemical load index
            2. WQI_Category    — WHO/Heliyon band label
            3. Microbial_Status— E. Coli / Total Coliform check
            4. Risk_Score      — Heliyon 2023 risk score (0–6)
            5. Risk_Category   — Heliyon 2023 risk label

        Method — worst-penalty wins:
        ─────────────────────────────
        Each dimension is translated to a penalty level (0–4).
        The composite class is the WORST (maximum) penalty
        across all five dimensions, so no single hazard can be
        masked by clean scores elsewhere.

        Penalty → Class:
            0 → Excellent
            1 → Good
            2 → Poor
            3 → Very Poor
            4 → Unsuitable

        Penalty tables:
        ┌─────────────────────────────┬─────────┐
        │ WQI_Calculated              │ Penalty │
        ├─────────────────────────────┼─────────┤
        │ 0 – 50   (Excellent)        │   0     │
        │ 51 – 100 (Good)             │   1     │
        │ 101 – 200 (Poor)            │   2     │
        │ 201 – 300 (Very Poor)       │   3     │
        │ > 300    (Unsuitable)       │   4     │
        └─────────────────────────────┴─────────┘
        ┌─────────────────────────────┬─────────┐
        │ WQI_Category                │ Penalty │
        ├─────────────────────────────┼─────────┤
        │ Excellent                   │   0     │
        │ Good                        │   1     │
        │ Poor                        │   2     │
        │ Very Poor                   │   3     │
        │ Unsuitable for drinking     │   4     │
        └─────────────────────────────┴─────────┘
        ┌─────────────────────────────┬─────────┐
        │ Microbial_Status            │ Penalty │
        ├─────────────────────────────┼─────────┤
        │ Safe                        │   0     │
        │ Contaminated                │   3     │
        └─────────────────────────────┴─────────┘
        ┌─────────────────────────────┬─────────┐
        │ Risk_Score                  │ Penalty │
        ├─────────────────────────────┼─────────┤
        │ 0  (Marginally Safe)        │   0     │
        │ 1  (Microbial only)         │   1     │
        │ 2  (TDS only)               │   1     │
        │ 3  (Single chemical)        │   2     │
        │ 4  (Chemical + microbial)   │   3     │
        │ 5  (Multiple chemical)      │   3     │
        │ 6  (Multi-chem + microbial) │   4     │
        └─────────────────────────────┴─────────┘
        ┌─────────────────────────────┬─────────┐
        │ Risk_Category               │ Penalty │
        ├─────────────────────────────┼─────────┤
        │ Marginally Safe             │   0     │
        │ Low                         │   1     │
        │ Medium                      │   2     │
        │ High                        │   3     │
        └─────────────────────────────┴─────────┘

        Required columns (must run after all prior steps):
            WQI_Calculated, WQI_Category, Microbial_Status,
            Risk_Score, Risk_Category

        Stores result in self.df['Water_Quality_Class'].
        """

        required = [
            'WQI_Calculated', 'WQI_Category',
            'Microbial_Status', 'Risk_Score', 'Risk_Category',
        ]
        missing = [c for c in required if c not in self.df.columns]
        if missing:
            raise RuntimeError(
                f"assign_water_quality_class() requires these columns to "
                f"be computed first: {missing}. Run the full pipeline."
            )

        def _wqi_score_penalty(wqi_val) -> int:
            """Penalty from raw WQI_Calculated value."""
            if pd.isna(wqi_val):
                return np.nan
            wqi_val = float(wqi_val)
            if wqi_val <= 50:
                return 0
            elif wqi_val <= 100:
                return 1
            elif wqi_val <= 200:
                return 2
            elif wqi_val <= 300:
                return 3
            else:
                return 4

        def _classify_row(row) -> str:
            penalties = []

            # ── Dimension 1: WQI_Calculated (raw numeric) ──────
            p1 = _wqi_score_penalty(row.get('WQI_Calculated'))
            if p1 is not np.nan and not (isinstance(p1, float) and np.isnan(p1)):
                penalties.append(int(p1))

            # ── Dimension 2: WQI_Category (label) ──────────────
            cat = row.get('WQI_Category')
            if pd.notna(cat):
                p2 = self._WQI_CATEGORY_PENALTY.get(str(cat))
                if p2 is not None:
                    penalties.append(p2)

            # ── Dimension 3: Microbial_Status ───────────────────
            mic = row.get('Microbial_Status')
            if pd.notna(mic):
                p3 = self._MICROBIAL_PENALTY.get(str(mic))
                if p3 is not None:
                    penalties.append(p3)

            # ── Dimension 4: Risk_Score ─────────────────────────
            rs = row.get('Risk_Score')
            if pd.notna(rs):
                p4 = self._RISK_SCORE_PENALTY.get(int(rs))
                if p4 is not None:
                    penalties.append(p4)

            # ── Dimension 5: Risk_Category ──────────────────────
            rc = row.get('Risk_Category')
            if pd.notna(rc):
                p5 = self._RISK_CATEGORY_PENALTY.get(str(rc))
                if p5 is not None:
                    penalties.append(p5)

            # ── Composite: worst penalty wins ───────────────────
            if not penalties:
                return np.nan

            worst = max(penalties)
            return self._PENALTY_TO_CLASS[worst]

        self.df['Water_Quality_Class'] = self.df.apply(_classify_row, axis=1)

        total = len(self.df)
        counts = self.df['Water_Quality_Class'].value_counts(dropna=False)

        print("\nComposite Water_Quality_Class Assigned:")
        print("-" * 45)
        class_order = ['Excellent', 'Good', 'Poor', 'Very Poor', 'Unsuitable']
        for cls in class_order:
            count = counts.get(cls, 0)
            pct   = count / total * 100 if total > 0 else 0
            print(f"  {cls:<15} : {count:>5}  ({pct:.1f}%)")
        nan_count = counts.get(np.nan, 0)
        if nan_count:
            print(f"  {'NaN':<15} : {nan_count:>5}  ({nan_count/total*100:.1f}%)")
        print("-" * 45)

        return self.df

    # ─────────────────────────────────────────────────────────────
    def compare_with_existing(self):
        """
        Compare calculated WQI with existing dataset WQI values.

        Metrics:
            - Correlation (r)
            - R² Score
            - Mean Absolute Error (MAE)
            - Root Mean Squared Error (RMSE)

        Also generates wqi_comparison.png
        """

        required_cols = ['WQI', 'WQI_Calculated']
        missing = [col for col in required_cols if col not in self.df.columns]

        if missing:
            print(f"Missing columns for comparison: {missing}")
            return

        compare_df = self.df[['WQI', 'WQI_Calculated']].copy()
        compare_df['WQI'] = pd.to_numeric(compare_df['WQI'], errors='coerce')
        compare_df['WQI_Calculated'] = pd.to_numeric(compare_df['WQI_Calculated'], errors='coerce')
        compare_df = compare_df.dropna()

        if len(compare_df) < 5:
            print("Not enough valid samples for comparison.")
            return

        actual = compare_df['WQI']
        predicted = compare_df['WQI_Calculated']

        corr = actual.corr(predicted)
        r2 = corr ** 2 if pd.notna(corr) else np.nan
        mae = (actual - predicted).abs().mean()
        rmse = np.sqrt(((actual - predicted) ** 2).mean())

        if pd.notna(r2):
            if r2 >= 0.90:
                agreement = "Excellent Agreement"
            elif r2 >= 0.75:
                agreement = "Strong Agreement"
            elif r2 >= 0.50:
                agreement = "Moderate Agreement"
            else:
                agreement = "Weak Agreement"
        else:
            agreement = "Unknown"

        print("\nWQI Model Validation")
        print("-" * 40)
        print(f"Samples Compared      : {len(compare_df)}")
        print(f"Correlation (r)       : {corr:.4f}" if pd.notna(corr) else "Correlation (r)       : NaN")
        print(f"R² Score              : {r2:.4f}" if pd.notna(r2) else "R² Score              : NaN")
        print(f"Mean Absolute Error   : {mae:.4f}")
        print(f"Root Mean Sq Error    : {rmse:.4f}")
        print(f"Model Agreement       : {agreement}")

        plt.figure(figsize=(8, 6))
        plt.scatter(actual, predicted, alpha=0.65, edgecolors='black')

        min_val = min(actual.min(), predicted.min())
        max_val = max(actual.max(), predicted.max())
        if min_val == max_val:
            min_val -= 1
            max_val += 1

        plt.plot([min_val, max_val], [min_val, max_val],
                 linestyle='--', linewidth=2, label='Perfect Agreement')
        plt.xlabel("Existing Dataset WQI")
        plt.ylabel("Calculated WQI")
        plt.title(
            f"WQI Model Validation\nr = {corr:.3f} | R² = {r2:.3f}"
            if pd.notna(corr) else "WQI Model Validation"
        )
        plt.legend()
        plt.tight_layout()

        save_path = os.path.join(self.output_dir, 'wqi_comparison.png')
        plt.savefig(save_path)
        plt.show()
        plt.close()
        print("\nSaved: wqi_comparison.png")

    # ─────────────────────────────────────────────────────────────
    def plot_wqi_distribution(self):
        """
        Plot WQI score distribution and category counts.

        Uses updated WQI thresholds:
            50, 100, 200, 300
        """

        if 'WQI_Calculated' not in self.df.columns:
            print("WQI_Calculated column not found.")
            return

        if self.df['WQI_Calculated'].dropna().empty:
            print("No WQI data available to plot.")
            return

        if 'WQI_Category' not in self.df.columns:
            print("WQI_Category column not found.")
            return

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # ── LEFT: WQI Distribution ────────────────────────────
        wqi_values = self.df['WQI_Calculated'].dropna()

        axes[0].hist(wqi_values, bins=30, edgecolor='black')

        thresholds = [
            (50,  'Excellent (0–50)'),
            (100, 'Good (51–100)'),
            (200, 'Poor (101–200)'),
            (300, 'Very Poor (201–300)'),
        ]

        for threshold, label in thresholds:
            axes[0].axvline(x=threshold, linestyle='--', linewidth=1.5, label=label)

        axes[0].set_title("WQI Score Distribution")
        axes[0].set_xlabel("Calculated WQI Score")
        axes[0].set_ylabel("Number of Samples")
        axes[0].legend(fontsize=8)

        # ── RIGHT: Category Counts ────────────────────────────
        category_order = ['Excellent', 'Good', 'Poor', 'Very Poor', 'Unsuitable for drinking']

        counts = (
            self.df['WQI_Category']
            .value_counts(dropna=False)
            .reindex(category_order, fill_value=0)
        )

        bars = axes[1].bar(counts.index, counts.values, edgecolor='black')

        category_colors = {
            'Excellent': 'green',
            'Good': 'blue',
            'Poor': 'orange',
            'Very Poor': 'red',
            'Unsuitable for drinking': 'purple',
        }

        for bar, category in zip(bars, counts.index):
            bar.set_color(category_colors.get(category, 'gray'))

        axes[1].set_title("Water Quality Categories")
        axes[1].set_xlabel("Category")
        axes[1].set_ylabel("Sample Count")
        axes[1].tick_params(axis='x', rotation=25)

        for i, val in enumerate(counts.values):
            axes[1].text(i, val + 0.5, str(val), ha='center', fontweight='bold')

        plt.suptitle(
            "Water Quality Index (WQI) Analysis\n"
            "WQI Classification — Heliyon 2023 / WHO Guidelines",
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout()

        save_path = os.path.join(self.output_dir, 'wqi_distribution.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
        print("\nSaved: wqi_distribution.png")

    # ─────────────────────────────────────────────────────────────
    def plot_wqi_by_province(self):
        """
        Plot average WQI score by province.

        Uses updated WQI thresholds: 50, 100, 200, 300
        """

        if 'Province' not in self.df.columns:
            print("Province column not found.")
            return

        if 'WQI_Calculated' not in self.df.columns:
            print("WQI_Calculated column not found.")
            return

        df_clean = self.df[['Province', 'WQI_Calculated']].dropna()

        if df_clean.empty:
            print("No valid data available.")
            return

        province_stats = (
            df_clean
            .groupby('Province')['WQI_Calculated']
            .agg(['mean', 'count'])
            .sort_values(by='mean', ascending=False)
        )

        province_stats = province_stats[province_stats['count'] >= 3]

        if province_stats.empty:
            print("Not enough samples per province.")
            return

        plt.figure(figsize=(12, 5))

        bars = plt.bar(province_stats.index, province_stats['mean'], edgecolor='black')

        for bar, val in zip(bars, province_stats['mean']):
            if val <= 50:
                bar.set_color('green')
            elif val <= 100:
                bar.set_color('blue')
            elif val <= 200:
                bar.set_color('orange')
            elif val <= 300:
                bar.set_color('red')
            else:
                bar.set_color('purple')

        thresholds = [
            (50,  'Excellent Threshold (50)'),
            (100, 'Good Threshold (100)'),
            (200, 'Poor Threshold (200)'),
            (300, 'Very Poor Threshold (300)'),
        ]

        for y, label in thresholds:
            plt.axhline(y=y, linestyle='--', linewidth=1.2, label=label)

        plt.title("Average Water Quality Index (WQI) by Province")
        plt.xlabel("Province")
        plt.ylabel("Average Calculated WQI")
        plt.xticks(rotation=30, ha='right')

        for i, val in enumerate(province_stats['mean']):
            plt.text(i, val + 1, f"{val:.1f}", ha='center', fontsize=9, fontweight='bold')

        plt.legend(fontsize=8)
        plt.tight_layout()

        save_path = os.path.join(self.output_dir, 'wqi_by_province.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
        print("\nSaved: wqi_by_province.png")

    # ─────────────────────────────────────────────────────────────
    def plot_wqi_by_resource_type(self):
        """
        Plot average WQI score by resource type.

        Uses updated WQI thresholds: 50, 100, 200, 300
        """

        if 'Resource Type' not in self.df.columns:
            print("Resource Type column not found.")
            return

        if 'WQI_Calculated' not in self.df.columns:
            print("WQI_Calculated column not found.")
            return

        df_clean = self.df[['Resource Type', 'WQI_Calculated']].dropna()

        if df_clean.empty:
            print("No valid data available.")
            return

        resource_stats = (
            df_clean
            .groupby('Resource Type')['WQI_Calculated']
            .agg(['mean', 'count'])
            .sort_values(by='mean', ascending=False)
        )

        resource_stats = resource_stats[resource_stats['count'] >= 3]

        if resource_stats.empty:
            print("Not enough samples per resource type.")
            return

        plt.figure(figsize=(12, 5))

        bars = plt.bar(resource_stats.index, resource_stats['mean'], edgecolor='black')

        for bar, val in zip(bars, resource_stats['mean']):
            if val <= 50:
                bar.set_color('green')
            elif val <= 100:
                bar.set_color('blue')
            elif val <= 200:
                bar.set_color('orange')
            elif val <= 300:
                bar.set_color('red')
            else:
                bar.set_color('purple')

        thresholds = [
            (50,  'Excellent Threshold (50)'),
            (100, 'Good Threshold (100)'),
            (200, 'Poor Threshold (200)'),
            (300, 'Very Poor Threshold (300)'),
        ]

        for y, label in thresholds:
            plt.axhline(y=y, linestyle='--', linewidth=1.2, label=label)

        plt.title("Average Water Quality Index (WQI)\nby Resource Type")
        plt.xlabel("Resource Type")
        plt.ylabel("Average Calculated WQI")
        plt.xticks(rotation=30, ha='right')

        for i, val in enumerate(resource_stats['mean']):
            plt.text(i, val + 1, f"{val:.1f}", ha='center', fontsize=9, fontweight='bold')

        plt.legend(fontsize=8)
        plt.tight_layout()

        save_path = os.path.join(self.output_dir, 'wqi_by_resource.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
        print("\nSaved: wqi_by_resource.png")

    # ─────────────────────────────────────────────────────────────
    def save_results(self):
        """
        Save WQI, microbial, risk, and composite class results
        to CSV with metadata.

        Exported columns:
            Province, City, Resource Type, Sampling Date,
            WQI_Calculated, WQI_Category,
            Microbial_Status,
            Risk_Score, Risk_Category,
            Water_Quality_Class
        """

        if self.df is None or self.df.empty:
            print("No data available to save.")
            return

        save_path = os.path.join(self.output_dir, 'wqi_results.csv')

        result_cols = [
            'Province', 'City', 'Resource Type', 'Sampling Date',
            'WQI_Calculated', 'WQI_Category',
            'Microbial_Status',
            'Risk_Score', 'Risk_Category',
            'Water_Quality_Class',        # composite target column
        ]

        available = [c for c in result_cols if c in self.df.columns]

        if not available:
            print("No relevant columns found to save.")
            return

        df_save = self.df[available].copy()

        sort_cols = [c for c in ['Province', 'City'] if c in df_save.columns]
        if sort_cols:
            df_save = df_save.sort_values(by=sort_cols)

        df_save.to_csv(save_path, index=False)
        print(f"Saved: {save_path}")
        print(f"Rows saved: {len(df_save)}")

        full_save_path = os.path.join(self.output_dir, 'wqi_full_dataset.csv')
        self.df.to_csv(full_save_path, index=False)
        print(f"Saved full dataset: {full_save_path}")

        metadata_path = os.path.join(self.output_dir, 'wqi_metadata.txt')
        with open(metadata_path, 'w') as f:
            f.write("WQI Calculation Metadata\n")
            f.write("=" * 40 + "\n")
            f.write(f"Total samples: {len(self.df)}\n")
            f.write(f"Columns exported: {available}\n")
            f.write(f"WQI parameters: {list(self.WHO_LIMITS.keys())}\n")
            f.write(f"Risk chemical parameters: {self.RISK_CHEMICAL_PARAMS}\n")
            f.write("\nWQI Category Scheme (Heliyon 2023 / WHO):\n")
            f.write("  0–50   : Excellent\n")
            f.write("  51–100 : Good\n")
            f.write("  101–200: Poor\n")
            f.write("  201–300: Very Poor\n")
            f.write("  >300   : Unsuitable for drinking\n")
            f.write("\nWater_Quality_Class — composite worst-penalty method:\n")
            f.write("  Inputs: WQI_Calculated, WQI_Category, Microbial_Status,\n")
            f.write("          Risk_Score, Risk_Category\n")
            f.write("  Logic : each dimension → penalty 0–4; class = max penalty\n")
            f.write("  0→Excellent  1→Good  2→Poor  3→Very Poor  4→Unsuitable\n")
        print(f"Saved metadata: {metadata_path}")

    # ─────────────────────────────────────────────────────────────
    def print_who_comparison(self):
        """
        Print WQI category distribution table using
        Heliyon 2023 / WHO classification scheme, including
        the composite Water_Quality_Class breakdown.
        """

        if 'WQI_Category' not in self.df.columns:
            print("WQI_Category column not found.")
            return

        counts = self.df['WQI_Category'].value_counts(dropna=False)
        total = counts.sum()

        if total == 0:
            print("No category data available.")
            return

        print("\n" + "=" * 65)
        print("   WQI CATEGORY DISTRIBUTION (Heliyon 2023 / WHO Guidelines)")
        print("=" * 65)
        print(f"  {'Category':<28} {'Range':>12} {'Count':>8}")
        print("-" * 65)

        ranges = {
            'Excellent':              '0 – 50',
            'Good':                   '51 – 100',
            'Poor':                   '101 – 200',
            'Very Poor':              '201 – 300',
            'Unsuitable for drinking': '> 300',
        }

        for cat, rng in ranges.items():
            count = counts.get(cat, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {cat:<28} {rng:>12} {count:>5} ({pct:.1f}%)")

        print("=" * 65)
        print(f"  {'TOTAL':<28} {'':>12} {total:>8}")
        print("=" * 65)

        # ── Microbial Status Summary ──────────────────────────
        if 'Microbial_Status' in self.df.columns:
            print("\n" + "=" * 65)
            print("   MICROBIAL STATUS DISTRIBUTION")
            print("=" * 65)
            mic_counts = self.df['Microbial_Status'].value_counts(dropna=False)
            for status, count in mic_counts.items():
                pct = (count / total * 100) if total > 0 else 0
                print(f"  {str(status):<28} {count:>5} ({pct:.1f}%)")
            print("=" * 65)

        # ── Risk Category Summary ──────────────────────────────
        if 'Risk_Category' in self.df.columns:
            print("\n" + "=" * 65)
            print("   RISK CATEGORY DISTRIBUTION (Heliyon 2023)")
            print("=" * 65)
            risk_order = ['Marginally Safe', 'Low', 'Medium', 'High']
            risk_counts = (
                self.df['Risk_Category']
                .value_counts(dropna=False)
                .reindex(risk_order, fill_value=0)
            )
            risk_ranges = {
                'Marginally Safe': 'Score 0',
                'Low':             'Score 1–2',
                'Medium':          'Score 3–4',
                'High':            'Score 5–6',
            }
            for cat, count in risk_counts.items():
                pct = (count / total * 100) if total > 0 else 0
                rng = risk_ranges.get(cat, '')
                print(f"  {cat:<28} {rng:>12} {count:>5} ({pct:.1f}%)")
            print("=" * 65)

        # ── Composite Water_Quality_Class Summary ─────────────
        if 'Water_Quality_Class' in self.df.columns:
            print("\n" + "=" * 65)
            print("   COMPOSITE Water_Quality_Class")
            print("   (worst-penalty across all 5 dimensions)")
            print("=" * 65)
            class_order = ['Excellent', 'Good', 'Poor', 'Very Poor', 'Unsuitable']
            class_counts = (
                self.df['Water_Quality_Class']
                .value_counts(dropna=False)
                .reindex(class_order, fill_value=0)
            )
            for cls, count in class_counts.items():
                pct = (count / total * 100) if total > 0 else 0
                print(f"  {cls:<28} {count:>5} ({pct:.1f}%)")
            print("=" * 65)

    # ─────────────────────────────────────────────────────────────
    def run_wqi_pipeline(self) -> pd.DataFrame:
        """
        Run complete WQI calculation pipeline.

        Pipeline order:
            1. calculate_wqi()
            2. assign_category()
            3. assign_microbial_status()
            4. calculate_risk_score()
            5. assign_risk_category()
            6. assign_water_quality_class()   ← NEW composite column
            7. compare_with_existing()        (optional)
            8. plot_wqi_distribution()
            9. plot_wqi_by_province()
           10. plot_wqi_by_resource_type()
           11. save_results()
           12. print_who_comparison()

        Returns:
            DataFrame with WQI_Calculated, WQI_Category,
            Microbial_Status, Risk_Score, Risk_Category,
            Water_Quality_Class
        """

        import time

        print("\n" + "=" * 55)
        print("     STEP 2: WQI CALCULATION PIPELINE")
        print("=" * 55)

        start_time = time.time()

        # ── 1: Calculate WQI ───────────────────────────
        try:
            print("\n[1] Calculating WQI...")
            self.calculate_wqi()
            print("✔ WQI calculation completed")
        except Exception as e:
            print(f"✖ WQI calculation failed: {e}")
            return self.df

        # ── 2: Assign WQI Categories ───────────────────
        try:
            print("\n[2] Assigning WQI categories...")
            self.assign_category()
            print("✔ WQI category assignment completed")
        except Exception as e:
            print(f"✖ Category assignment failed: {e}")

        # ── 3: Microbial Status ────────────────────────
        try:
            print("\n[3] Assigning microbial status...")
            self.assign_microbial_status()
            print("✔ Microbial status assignment completed")
        except Exception as e:
            print(f"✖ Microbial status assignment failed: {e}")

        # ── 4: Risk Score ──────────────────────────────
        try:
            print("\n[4] Calculating risk scores...")
            self.calculate_risk_score()
            print("✔ Risk score calculation completed")
        except Exception as e:
            print(f"✖ Risk score calculation failed: {e}")

        # ── 5: Risk Category ───────────────────────────
        try:
            print("\n[5] Assigning risk categories...")
            self.assign_risk_category()
            print("✔ Risk category assignment completed")
        except Exception as e:
            print(f"✖ Risk category assignment failed: {e}")

        # ── 6: Composite Water_Quality_Class ───────────
        try:
            print("\n[6] Assigning composite Water_Quality_Class...")
            self.assign_water_quality_class()
            print("✔ Water_Quality_Class assignment completed")
        except Exception as e:
            print(f"✖ Water_Quality_Class assignment failed: {e}")

        # ── 7: Comparison (optional) ───────────────────
        try:
            print("\n[7] Comparing with existing WQI...")
            self.compare_with_existing()
        except Exception as e:
            print(f"⚠ Comparison skipped: {e}")

        # ── 8–10: Visualizations ───────────────────────
        try:
            print("\n[8] Generating plots...")
            self.plot_wqi_distribution()
            self.plot_wqi_by_province()
            self.plot_wqi_by_resource_type()
            print("✔ Plots generated")
        except Exception as e:
            print(f"⚠ Plotting partially failed: {e}")

        # ── 11: Save Results ───────────────────────────
        try:
            print("\n[9] Saving results...")
            self.save_results()
            print("✔ Results saved")
        except Exception as e:
            print(f"⚠ Saving failed: {e}")

        # ── 12: Summary Report ─────────────────────────
        try:
            print("\n[10] Printing summary...")
            self.print_who_comparison()
        except Exception as e:
            print(f"⚠ Summary failed: {e}")

        total_time = time.time() - start_time
        print("\n" + "=" * 55)
        print(f" Pipeline completed in {total_time:.2f} seconds")
        print("=" * 55)

        return self.df

    # ─────────────────────────────────────────────────────────────
    def get_dataframe(self) -> pd.DataFrame:
        """Return a safe copy of DataFrame with all results."""
        if self.df is None or self.df.empty:
            print("No data available.")
            return pd.DataFrame()
        return self.df.copy()