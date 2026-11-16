"""
Step_4_DataTransformation.py

Prepares the dataset for machine learning by:
    1. Outlier treatment using IQR capping
    2. Encoding categorical columns
    3. Scaling numeric features
    4. Dropping columns not needed for ML
    5. Saving transformed data to CSV
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
import os


class DataTransformation:
    """
    Transforms the prepared dataset into a format
    ready for feature selection and ML training.

    Attributes:
        df              (DataFrame) : Input DataFrame
        output_dir      (str)       : Folder for outputs
        df_transformed  (DataFrame) : Final transformed data
        scaler          (obj)       : Fitted StandardScaler
        label_encoders  (dict)      : Fitted LabelEncoders
    """

    # Parameters to apply IQR capping on
    PARAMETER_COLS = [
        'pH', 'Turbidity (NTU)', 'EC (µS/cm)',
        'TDS (mg/L)', 'Hardness (mg/L)',
        'Calcium (mg/L)', 'Magnesium (mg/L)',
        'Sodium (mg/L)', 'Potassium (mg/L)',
        'Chloride (mg/L)', 'Sulfate (mg/L)',
        'Nitrate (mg/L)', 'Fluoride (mg/L)',
        'Iron (mg/L)', 'Arsenic (mg/L)','Total Coliform','E. Coli',
        'WQI_Calculated'
    ]

    # Categorical columns to encode
    CATEGORICAL_COLS = [
        'Province',
        'City',
        'Resource Type'
    ]

    # Columns to exclude from scaling
    # (target, identifiers, already encoded cats)
    EXCLUDE_FROM_SCALE = [
        'WQI_Category',
        'WQI',
        'Water_Quality_Class',
        'Sampling Date',
        'Microbial_Status'
        'Risk_Category',
    ]

    def __init__(
        self,
        df: pd.DataFrame,
        output_dir: str = './TransformedData'
    ):
        """
        Initialize DataTransformation.

        Args:
            df         : DataFrame from Step 2 (with WQI)
            output_dir : Folder to save outputs
        """
        self.df             = df.copy()
        self.output_dir     = output_dir
        self.df_transformed = None
        self.scaler         = StandardScaler()
        self.label_encoders = {}

        os.makedirs(self.output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────
    def apply_iqr_capping(self):
        """
        Cap outliers using IQR method (Winsorization).

        Values below Q1 - 1.5*IQR are set to lower bound.
        Values above Q3 + 1.5*IQR are set to upper bound.

        This preserves all 706 rows while controlling
        extreme values that distort model training.
        """
        print("\nApplying IQR capping on parameters...")

        available = [
            c for c in self.PARAMETER_COLS
            if c in self.df.columns
        ]

        cap_summary = []

        for col in available:
            Q1  = self.df[col].quantile(0.25)
            Q3  = self.df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            n_lower = (self.df[col] < lower).sum()
            n_upper = (self.df[col] > upper).sum()

            self.df[col] = self.df[col].clip(
                lower=lower, upper=upper
            )

            cap_summary.append({
                'Parameter' : col,
                'Lower_Cap' : round(lower, 4),
                'Upper_Cap' : round(upper, 4),
                'Capped_Low': n_lower,
                'Capped_High': n_upper,
                'Total_Capped': n_lower + n_upper
            })

        cap_df = pd.DataFrame(cap_summary)
        cap_df.to_csv(
            os.path.join(self.output_dir, 'iqr_capping_summary.csv'),
            index=False
        )

        print("IQR Capping Summary:")
        print(cap_df[
            ['Parameter', 'Total_Capped',
             'Lower_Cap', 'Upper_Cap']
        ].to_string(index=False))
        print("Saved: iqr_capping_summary.csv")

    # ─────────────────────────────────────────────────────────────
    def plot_before_after_capping(self):
        """
        Plot boxplots before and after IQR capping
        for key parameters to verify outlier treatment.
        """
        # Reload original to compare
        key_params = [
            'Arsenic (mg/L)', 'Iron (mg/L)',
            'Sodium (mg/L)', 'TDS (mg/L)',
            'Chloride (mg/L)', 'Magnesium (mg/L)'
        ]
        available = [
            p for p in key_params if p in self.df.columns
        ]

        fig, axes = plt.subplots(
            2, len(available),
            figsize=(18, 8)
        )

        for i, col in enumerate(available):
            # After capping (current df)
            axes[0][i].boxplot(
                self.df[col].dropna(),
                patch_artist=True,
                boxprops=dict(facecolor='lightgreen')
            )
            axes[0][i].set_title(
                col.replace(' (mg/L)', ''), fontsize=9
            )
            axes[0][i].set_ylabel('Value')

            # Distribution after capping
            axes[1][i].hist(
                self.df[col].dropna(),
                bins=20, color='steelblue',
                edgecolor='black', alpha=0.8
            )
            axes[1][i].set_title(
                f'Distribution after capping', fontsize=8
            )

        axes[0][0].set_ylabel('After IQR Capping')
        axes[1][0].set_ylabel('Distribution')

        plt.suptitle(
            'Key Parameters After IQR Capping',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'after_iqr_capping.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: after_iqr_capping.png")

    # ─────────────────────────────────────────────────────────────
    def encode_categorical(self):
        """
        Encode categorical columns using LabelEncoder.

        Columns encoded:
            Province     : AJK=0, Balochistan=1 ...
            City         : city names to integers
            Resource Type: Groundwater=0, Tap Water=1 ...

        Encoders are stored for later use in prediction.
        """
        print("\nEncoding categorical columns...")

        available = [
            c for c in self.CATEGORICAL_COLS
            if c in self.df.columns
        ]

        for col in available:
            le = LabelEncoder()
            self.df[col] = le.fit_transform(
                self.df[col].astype(str)
            )
            self.label_encoders[col] = le

            print(f"  {col} encoded:")
            for i, cls in enumerate(le.classes_):
                print(f"    {cls} -> {i}")

        print("Categorical encoding complete.")

    # ─────────────────────────────────────────────────────────────
    def scale_numeric_features(self):
        """
        Apply StandardScaler to all numeric feature columns.

        StandardScaler converts values to zero mean and
        unit variance. This ensures no single parameter
        dominates due to its scale.

        Excluded from scaling:
            Water_Quality_Class    - target column
            WQI             - original WQI (reference only)
            Water Quality Class - original labels
            Sampling Date   - year identifier
        """
        print("\nScaling numeric features...")

        # Get all numeric columns
        numeric_cols = self.df.select_dtypes(
            include=[np.number]
        ).columns.tolist()

        # Remove excluded columns
        scale_cols = [
            c for c in numeric_cols
            if c not in self.EXCLUDE_FROM_SCALE
        ]

        print(f"  Scaling {len(scale_cols)} columns:")
        for c in scale_cols:
            print(f"    -> {c}")

        self.df[scale_cols] = self.scaler.fit_transform(
            self.df[scale_cols]
        )

        print("Scaling complete.")

    # ─────────────────────────────────────────────────────────────
    def save_transformed_data(self):
        """Save fully transformed DataFrame to CSV."""
        save_path = os.path.join(
            self.output_dir,
            'transformed_data.csv'
        )
        self.df.to_csv(save_path, index=False)
        print(f"Saved: transformed_data.csv")
        print(f"Shape: {self.df.shape}")

    # ─────────────────────────────────────────────────────────────
    def print_summary(self):
        """Print transformation summary."""
        print("\n" + "="*55)
        print("     DATA TRANSFORMATION SUMMARY")
        print("="*55)
        print(f"  Shape          : {self.df.shape}")
        print(f"\n  Columns:")
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            print(f"    -> {col:<35} [{dtype}]")
        print(f"\n  Missing values : {self.df.isna().sum().sum()}")
        print("="*55)

    # ─────────────────────────────────────────────────────────────
    def run_transformation(self) -> pd.DataFrame:
        """
        Run complete data transformation pipeline.

        Steps:
            1. IQR capping (outlier treatment)
            2. Plot before/after capping
            3. Encode categorical columns
            4. Scale numeric features
            5. Save transformed data
            6. Print summary

        Returns:
            Fully transformed DataFrame
        """
        print("\n" + "="*55)
        print("     STEP 4: DATA TRANSFORMATION")
        print("="*55)

        self.apply_iqr_capping()
        self.plot_before_after_capping()
        self.encode_categorical()
        self.scale_numeric_features()
        self.save_transformed_data()
        self.print_summary()

        self.df_transformed = self.df

        print("\nStep 4 — Data Transformation COMPLETE!")
        return self.df_transformed

    # ─────────────────────────────────────────────────────────────
    def get_dataframe(self) -> pd.DataFrame:
        """Return transformed DataFrame."""
        return self.df_transformed

    def get_scaler(self) -> StandardScaler:
        """Return fitted scaler for later use."""
        return self.scaler

    def get_label_encoders(self) -> dict:
        """Return fitted label encoders for later use."""
        return self.label_encoders