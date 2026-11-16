"""
Step_1_DataPreparation.py

Handles all data loading, cleaning and preparation
for the Water Quality Classification Project.

Tasks:
    - Load Excel dataset
    - Fix BDL (Below Detection Limit) values
    - Standardize inconsistent text values
    - Handle missing values
    - Remove duplicates
    - Drop useless columns
    - Prune low quality samples
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
import os


class DataPreparation:
    """
    Loads and prepares the water quality dataset.

    Attributes:
        file_path   (str)       : Path to Excel file
        output_dirs (dict)      : Output folder paths
        df          (DataFrame) : Cleaned dataframe
    """

    # Water quality parameter columns
    PARAMETER_COLS = [
        'pH', 'Turbidity (NTU)', 'EC (µS/cm)',
        'TDS (mg/L)', 'Hardness (mg/L)',
        'Calcium (mg/L)', 'Magnesium (mg/L)',
        'Sodium (mg/L)', 'Potassium (mg/L)',
        'Chloride (mg/L)', 'Sulfate (mg/L)',
        'Nitrate (mg/L)', 'Fluoride (mg/L)',
        'Iron (mg/L)', 'Arsenic (mg/L)','Total Coliform','E. Coli'
    ]

    # Columns not useful for ML
    DROP_COLS = [
        'Country',
        'District/Area',
        'Reference',
        'Sample_ID'
    ]

    def __init__(self, file_path: str, output_dirs: dict = None):
        """
        Initialize DataPreparation.

        Args:
            file_path   : Path to Excel dataset
            output_dirs : Dictionary of output folder paths
        """
        self.file_path = file_path
        self.df = None

        if output_dirs is None:
            self.output_dirs = {
                'MissingValuegraph' : './MissingValuegraph',
                'EDA'               : './EDA',
                'WQIResults'        : './WQIResults',
                'FeatureSelection'  : './FeatureSelection',
                'ModelTraining'     : './ModelTraining',
                'ModelComparison'   : './ModelComparison',
                'Models'            : './Models',
            }
        else:
            self.output_dirs = output_dirs

    # ─────────────────────────────────────────────────────────────
    def create_directories(self):
        """Create all output directories if not exist."""
        for path in self.output_dirs.values():
            os.makedirs(path, exist_ok=True)
        print("Output directories created.")

    # ─────────────────────────────────────────────────────────────
    def load_data(self) -> pd.DataFrame:
        """
        Load dataset from Excel file.

        Returns:
            Raw DataFrame
        """
        print("\nLoading dataset...")
        self.df = pd.read_excel(
            self.file_path,
            sheet_name='merged_file.csv'
        )
        print(f"Loaded: {self.df.shape[0]} rows, "
              f"{self.df.shape[1]} columns")
        return self.df

    # ─────────────────────────────────────────────────────────────
    def fix_bdl_values(self):
        """
        Replace BDL (Below Detection Limit) with 0.0.

        BDL means the instrument could not detect the
        substance — it is effectively zero or trace.
        """
        bdl_count = 0

        for col in self.PARAMETER_COLS:
            if col not in self.df.columns:
                continue

            # Count BDL
            mask = self.df[col].astype(str).str.upper() == 'BDL'
            bdl_count += mask.sum()

            # Replace BDL → 0 then convert to numeric
            self.df[col] = (
                self.df[col]
                .replace({'BDL': 0, 'bdl': 0, 'Bdl': 0})
            )
            self.df[col] = pd.to_numeric(
                self.df[col], errors='coerce'
            )

        print(f"BDL values fixed: {bdl_count} replaced with 0")

    # ─────────────────────────────────────────────────────────────
    def standardize_text(self):
        """
        Fix inconsistent text in categorical columns.

        Examples:
            'Ground water' → 'Groundwater'
            'KPK' → 'Khyber Pakhtunkhwa'
            'surfacewater' → 'Surface Water'
        """
        # Fix Resource Type
        resource_map = {
            'Ground water'   : 'Groundwater',
            'Drinking water' : 'Drinking Water',
            'surfacewater'   : 'Surface Water',
        }
        self.df['Resource Type'] = (
            self.df['Resource Type']
            .str.strip()
            .replace(resource_map)
        )

        # Fix Province names
        province_map = {
            'KPK' : 'Khyber Pakhtunkhwa',
        }
        self.df['Province'] = (
            self.df['Province']
            .str.strip()
            .replace(province_map)
        )

        # Sampling Date → integer year
        self.df['Sampling Date'] = pd.to_numeric(
            self.df['Sampling Date'], errors='coerce'
        ).astype('Int64')

        print("Text values standardized.")
        print("   Resource Types:",
              sorted(self.df['Resource Type'].unique().tolist()))
        print("   Provinces:",
              sorted(self.df['Province'].unique().tolist()))

    # ─────────────────────────────────────────────────────────────
    def remove_duplicates(self):
        """Remove duplicate rows."""
        before = len(self.df)
        self.df = self.df.drop_duplicates().reset_index(drop=True)
        after = len(self.df)
        print(f"Duplicates removed: {before - after} rows dropped")

    # ─────────────────────────────────────────────────────────────
    def drop_useless_columns(self):
        """
        Drop columns not useful for ML analysis.

        Dropped:
            Country      - all Pakistan, no variation
            District/Area - 76% missing
            Reference    - citation text only
            Sample_ID    - just a row identifier
        """
        cols = [c for c in self.DROP_COLS if c in self.df.columns]
        self.df = self.df.drop(columns=cols)
        print(f"Dropped: {cols}")

    # ─────────────────────────────────────────────────────────────
    def handle_missing_values(self):
        """
        Plot and handle missing values.

        Strategy:
            - Numeric columns → impute with median
            - WQI/Class → left as is (calculated in Step 2)
        """
        # Plot BEFORE
        plt.figure(figsize=(14, 5))
        miss = self.df.isna().sum()
        miss[miss > 0].plot(kind='bar', color='steelblue',
                            edgecolor='black')
        plt.title('Missing Values — Before Treatment', fontsize=14)
        plt.ylabel('Missing Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(
            self.output_dirs['MissingValuegraph'],
            'missing_before.png'))
        plt.show()
        plt.close()

        print("\nMissing Values BEFORE:")
        print(miss[miss > 0].to_string())

        # Impute numeric columns (except WQI + Date)
        skip = ['WQI', 'Sampling Date']
        num_cols = [
            c for c in self.df.select_dtypes(
                include=[np.number]).columns
            if c not in skip
        ]
        imputer = SimpleImputer(strategy='median')
        self.df[num_cols] = imputer.fit_transform(self.df[num_cols])

        # Plot AFTER
        plt.figure(figsize=(14, 5))
        miss_after = self.df.isna().sum()
        miss_after.plot(kind='bar', color='lightgreen',
                        edgecolor='black')
        plt.title('Missing Values — After Treatment', fontsize=14)
        plt.ylabel('Missing Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(
            self.output_dirs['MissingValuegraph'],
            'missing_after.png'))
        plt.show()
        plt.close()

        print("\nMissing Values AFTER:")
        remaining = miss_after[miss_after > 0]
        print(remaining.to_string() if len(remaining) > 0
              else "  None remaining in numeric columns ✅")
        print("Missing values handled.")

    # ─────────────────────────────────────────────────────────────
    def prune_low_quality_samples(self, min_params: int = 8):
        """
        Remove samples with too few measured parameters.

        A sample needs at least min_params non-null values
        among the water quality parameters to be reliable.

        Args:
            min_params : Minimum required non-null parameters
        """
        before = len(self.df)

        # Count available parameters per row
        available = [
            c for c in self.PARAMETER_COLS
            if c in self.df.columns
        ]
        param_count = self.df[available].notna().sum(axis=1)

        self.df = self.df[
            param_count >= min_params
        ].reset_index(drop=True)

        after = len(self.df)

        print(f"\nPruning complete:")
        print(f"   Before : {before} samples")
        print(f"   Pruned : {before - after} samples removed")
        print(f"   After  : {after} samples remaining")
        print(f"   Rule   : kept samples with >= {min_params} "
              f"parameters measured")

    # ─────────────────────────────────────────────────────────────
    def print_summary(self):
        """Print final dataset summary."""
        print("\n" + "="*55)
        print("     DATA PREPARATION SUMMARY")
        print("="*55)
        print(f"  Shape          : {self.df.shape}")
        print(f"\n  Columns:")
        for col in self.df.columns:
            print(f"    → {col}")
        print(f"\n  Missing Values:")
        miss = self.df.isna().sum()
        miss_cols = miss[miss > 0]
        if len(miss_cols) > 0:
            print(miss_cols.to_string())
        else:
            print("    None in numeric columns ")
        print("="*55)

    # ─────────────────────────────────────────────────────────────
    def run_pipeline(self) -> pd.DataFrame:
        """
        Run complete data preparation pipeline.

        Returns:
            Cleaned and prepared DataFrame
        """
        print("\n" + "="*55)
        print("     STEP 1: DATA PREPARATION")
        print("="*55)

        self.create_directories()
        self.load_data()
        self.fix_bdl_values()
        self.standardize_text()
        self.remove_duplicates()
        self.drop_useless_columns()
        self.handle_missing_values()
        self.prune_low_quality_samples(min_params=8)
        self.print_summary()

        print("\nStep 1 — Data Preparation COMPLETE!")
        return self.df

    # ─────────────────────────────────────────────────────────────
    def get_dataframe(self) -> pd.DataFrame:
        """Return prepared DataFrame."""
        return self.df