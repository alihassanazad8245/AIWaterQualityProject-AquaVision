"""
Step_6_TrainTestSplit.py

Splits the dataset into training and testing sets
for model training and evaluation.

Key considerations:
    - Stratified split to preserve class distribution
    - 80% training / 20% testing
    - Class imbalance noted and handled here
    - Saves split statistics for reference
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os


class TrainTestSplit:
    """
    Prepares final X, y arrays and performs stratified
    train/test split for classification.

    Attributes:
        df               (DataFrame) : Transformed DataFrame
        selected_features (list)     : Features from Step 5
        output_dir       (str)       : Folder for outputs
        X_train, X_test  (DataFrame) : Split feature sets
        y_train, y_test  (array)     : Split target arrays
        class_names      (list)      : Original class labels
    """

    TARGET_COL = 'Water_Quality_Class'

    def __init__(
        self,
        df: pd.DataFrame,
        selected_features: list,
        output_dir: str = './ModelTraining'
    ):
        """
        Initialize TrainTestSplit.

        Args:
            df               : Transformed DataFrame
            selected_features: List of feature column names
            output_dir       : Folder to save split info
        """
        self.df               = df.copy()
        self.selected_features = selected_features
        self.output_dir       = output_dir

        self.X_train = None
        self.X_test  = None
        self.y_train = None
        self.y_test  = None

        self.label_encoder = LabelEncoder()
        self.class_names   = []

        os.makedirs(self.output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────
    def prepare_X_y(self):
        """
        Extract feature matrix X and target vector y.
        Drops rows where target label is missing.

        Returns:
            X (DataFrame), y (array)
        """
        # Drop rows without target label
        df_clean = self.df.dropna(
            subset=[self.TARGET_COL]
        ).reset_index(drop=True)

        print(f"Total labeled samples : {len(df_clean)}")

        # Features
        available = [
            f for f in self.selected_features
            if f in df_clean.columns
        ]
        X = df_clean[available].copy()

        # Target — encode to integers
        y_raw = df_clean[self.TARGET_COL].copy()
        y     = self.label_encoder.fit_transform(y_raw)

        self.class_names = list(self.label_encoder.classes_)

        print(f"Features used         : {len(available)}")
        print(f"Target classes        : {self.class_names}")
        print(f"\nClass distribution:")
        counts = pd.Series(y_raw).value_counts()
        for cls, cnt in counts.items():
            pct = cnt / len(y_raw) * 100
            print(f"  {cls:<25} {cnt:>4} ({pct:.1f}%)")

        return X, y

    # ─────────────────────────────────────────────────────────────
    def split(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.20,
        random_state: int = 42
    ):
        """
        Perform stratified train/test split.

        Stratified means each class keeps the same
        proportion in both train and test sets.
        This is critical with imbalanced classes.

        Args:
            X            : Feature matrix
            y            : Encoded target array
            test_size    : Fraction for test set (0.20 = 20%)
            random_state : Random seed for reproducibility

        Returns:
            X_train, X_test, y_train, y_test
        """
        self.X_train, self.X_test, \
        self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y
        )

        print(f"\nTrain/Test Split (stratified):")
        print(f"  Total samples : {len(X)}")
        print(f"  Train set     : {len(self.X_train)} "
              f"({len(self.X_train)/len(X)*100:.1f}%)")
        print(f"  Test set      : {len(self.X_test)} "
              f"({len(self.X_test)/len(X)*100:.1f}%)")

        return (
            self.X_train, self.X_test,
            self.y_train, self.y_test
        )

    # ─────────────────────────────────────────────────────────────
    def plot_split_distribution(self):
        """
        Plot class distribution in train vs test sets
        to verify stratification is correct.
        """
        train_counts = pd.Series(
            self.label_encoder.inverse_transform(self.y_train)
        ).value_counts()

        test_counts = pd.Series(
            self.label_encoder.inverse_transform(self.y_test)
        ).value_counts()

        # Align both series to same index
        all_classes = sorted(
            set(train_counts.index) | set(test_counts.index)
        )
        train_counts = train_counts.reindex(
            all_classes, fill_value=0
        )
        test_counts  = test_counts.reindex(
            all_classes, fill_value=0
        )

        x     = np.arange(len(all_classes))
        width = 0.35

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Left: Count comparison
        axes[0].bar(
            x - width/2, train_counts.values,
            width, label='Train',
            color='steelblue', edgecolor='black'
        )
        axes[0].bar(
            x + width/2, test_counts.values,
            width, label='Test',
            color='coral', edgecolor='black'
        )
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(
            all_classes, rotation=30, ha='right', fontsize=9
        )
        axes[0].set_title('Class Count: Train vs Test')
        axes[0].set_ylabel('Count')
        axes[0].legend()

        for i, (tr, te) in enumerate(
            zip(train_counts.values, test_counts.values)
        ):
            axes[0].text(
                i - width/2, tr + 0.2, str(tr),
                ha='center', fontsize=8
            )
            axes[0].text(
                i + width/2, te + 0.2, str(te),
                ha='center', fontsize=8
            )

        # Right: Percentage comparison
        train_pct = train_counts / train_counts.sum() * 100
        test_pct  = test_counts  / test_counts.sum()  * 100

        axes[1].bar(
            x - width/2, train_pct.values,
            width, label='Train',
            color='steelblue', edgecolor='black'
        )
        axes[1].bar(
            x + width/2, test_pct.values,
            width, label='Test',
            color='coral', edgecolor='black'
        )
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(
            all_classes, rotation=30, ha='right', fontsize=9
        )
        axes[1].set_title(
            'Class Proportion: Train vs Test (%)'
        )
        axes[1].set_ylabel('Percentage (%)')
        axes[1].legend()

        plt.suptitle(
            'Stratified Train/Test Split Verification',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'train_test_split_distribution.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: train_test_split_distribution.png")

    # ─────────────────────────────────────────────────────────────
    def save_split_info(self):
        """Save split statistics to CSV for reference."""
        train_counts = pd.Series(
            self.label_encoder.inverse_transform(self.y_train)
        ).value_counts()

        test_counts = pd.Series(
            self.label_encoder.inverse_transform(self.y_test)
        ).value_counts()

        all_classes = sorted(
            set(train_counts.index) | set(test_counts.index)
        )
        train_counts = train_counts.reindex(
            all_classes, fill_value=0
        )
        test_counts  = test_counts.reindex(
            all_classes, fill_value=0
        )

        info_df = pd.DataFrame({
            'Class'      : all_classes,
            'Train_Count': train_counts.values,
            'Test_Count' : test_counts.values,
            'Train_Pct'  : (
                train_counts / train_counts.sum() * 100
            ).round(2).values,
            'Test_Pct'   : (
                test_counts / test_counts.sum() * 100
            ).round(2).values,
        })

        save_path = os.path.join(
            self.output_dir, 'split_info.csv'
        )
        info_df.to_csv(save_path, index=False)
        print(f"Saved: split_info.csv")

    # ─────────────────────────────────────────────────────────────
    def print_summary(self):
        """Print final split summary."""
        print("\n" + "="*55)
        print("     TRAIN/TEST SPLIT SUMMARY")
        print("="*55)
        print(f"  Features    : {self.X_train.shape[1]}")
        print(f"  Train rows  : {self.X_train.shape[0]}")
        print(f"  Test rows   : {self.X_test.shape[0]}")
        print(f"  Classes     : {len(self.class_names)}")
        print(f"\n  Train class distribution:")

        train_series = pd.Series(
            self.label_encoder.inverse_transform(self.y_train)
        ).value_counts()

        for cls, cnt in train_series.items():
            pct = cnt / len(self.y_train) * 100
            print(f"    {cls:<25} {cnt:>4} ({pct:.1f}%)")

        print(f"\n  Test class distribution:")
        test_series = pd.Series(
            self.label_encoder.inverse_transform(self.y_test)
        ).value_counts()

        for cls, cnt in test_series.items():
            pct = cnt / len(self.y_test) * 100
            print(f"    {cls:<25} {cnt:>4} ({pct:.1f}%)")

        print("="*55)

    # ─────────────────────────────────────────────────────────────
    def run_split(self):
        """
        Run complete train/test split pipeline.

        Returns:
            X_train, X_test, y_train, y_test,
            class_names, label_encoder
        """
        print("\n" + "="*55)
        print("     STEP 6: TRAIN/TEST SPLIT")
        print("="*55)

        X, y = self.prepare_X_y()
        self.split(X, y, test_size=0.20, random_state=42)
        self.plot_split_distribution()
        self.save_split_info()
        self.print_summary()

        print("\nStep 6 — Train/Test Split COMPLETE!")

        return (
            self.X_train, self.X_test,
            self.y_train, self.y_test,
            self.class_names,
            self.label_encoder
        )

    # ─────────────────────────────────────────────────────────────
    def get_splits(self):
        """Return all split arrays."""
        return (
            self.X_train, self.X_test,
            self.y_train, self.y_test
        )

    def get_class_names(self) -> list:
        """Return original class label names."""
        return self.class_names

    def get_label_encoder(self):
        """Return fitted label encoder."""
        return self.label_encoder