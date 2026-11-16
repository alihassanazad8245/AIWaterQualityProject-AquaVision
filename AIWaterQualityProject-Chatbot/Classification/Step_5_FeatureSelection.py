"""
Step_5_FeatureSelection.py

Selects the most important features for predicting
WQI_Category using three methods:

    1. Correlation analysis with target
    2. SelectKBest (chi2 / f_classif)
    3. Random Forest feature importance

Final features are selected based on agreement
across all three methods.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import os


class FeatureSelection:
    """
    Identifies most important features for WQI_Category
    classification using multiple selection methods.

    Attributes:
        df              (DataFrame) : Transformed DataFrame
        output_dir      (str)       : Folder for outputs
        selected_features (list)    : Final selected features
        target_col      (str)       : Target column name
    """

    # All candidate feature columns
    FEATURE_COLS = [
        'pH', 'Turbidity (NTU)', 'EC (µS/cm)',
        'TDS (mg/L)', 'Hardness (mg/L)',
        'Calcium (mg/L)', 'Magnesium (mg/L)',
        'Sodium (mg/L)', 'Potassium (mg/L)',
        'Chloride (mg/L)', 'Sulfate (mg/L)',
        'Nitrate (mg/L)', 'Fluoride (mg/L)',
        'Iron (mg/L)', 'Arsenic (mg/L)','Total Coliform','E. Coli',
        'Province', 'Resource Type'
    ]

    TARGET_COL = 'Water_Quality_Class'

    def __init__(
        self,
        df: pd.DataFrame,
        output_dir: str = './FeatureSelection'
    ):
        """
        Initialize FeatureSelection.

        Args:
            df         : Transformed DataFrame from Step 4
            output_dir : Folder to save plots and CSVs
        """
        self.df               = df.copy()
        self.output_dir       = output_dir
        self.selected_features = []
        self.X                = None
        self.y                = None
        self.y_encoded        = None
        self.target_encoder   = LabelEncoder()

        os.makedirs(self.output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────
    def prepare_X_y(self):
        """
        Prepare feature matrix X and target vector y.
        Drops rows where Water_Quality_Class is missing.
        """
        # Get available feature columns
        available = [
            c for c in self.FEATURE_COLS
            if c in self.df.columns
        ]

        # Drop rows where target is missing
        df_clean = self.df.dropna(
            subset=[self.TARGET_COL]
        ).reset_index(drop=True)

        print(f"Rows with Water_Quality_Class label: {len(df_clean)}")

        self.X = df_clean[available].copy()
        self.y = df_clean[self.TARGET_COL].copy()

        # Encode target for sklearn methods
        self.y_encoded = self.target_encoder.fit_transform(self.y)

        print(f"Features available : {len(available)}")
        print(f"Target classes     : "
              f"{list(self.target_encoder.classes_)}")

        return self.X, self.y_encoded

    # ─────────────────────────────────────────────────────────────
    def method1_correlation(self) -> pd.Series:
        """
        Method 1: Correlation-based feature selection.

        Encodes target numerically and computes absolute
        Pearson correlation of each feature with target.

        Returns:
            Series of correlation scores sorted descending
        """
        print("\n--- Method 1: Correlation Analysis ---")

        # Encode target to numeric for correlation
        df_corr = self.X.copy()
        df_corr['Target'] = self.y_encoded

        corr = df_corr.corr()['Target'].drop('Target')
        corr_abs = corr.abs().sort_values(ascending=False)

        # Save
        corr_abs.to_frame('Correlation').to_csv(
            os.path.join(
                self.output_dir,
                'method1_correlation.csv'
            )
        )

        # Plot
        plt.figure(figsize=(12, 6))
        colors = [
            'steelblue' if v > 0.1 else 'lightgray'
            for v in corr_abs.values
        ]
        plt.bar(
            corr_abs.index,
            corr_abs.values,
            color=colors, edgecolor='black'
        )
        plt.axhline(
            y=0.1, color='red', linestyle='--',
            linewidth=1.5, label='Threshold = 0.10'
        )
        plt.title(
            'Method 1: Feature Correlation with Water_Quality_Class',
            fontsize=13
        )
        plt.xlabel('Feature')
        plt.ylabel('Absolute Correlation')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'method1_correlation.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()

        print("Top features by correlation:")
        print(corr_abs.head(10).to_string())
        print("Saved: method1_correlation.png")

        return corr_abs

    # ─────────────────────────────────────────────────────────────
    def method2_selectkbest(self) -> pd.Series:
        """
        Method 2: SelectKBest using f_classif (ANOVA F-test).

        Computes F-statistic for each feature vs target.
        Higher F-score = more discriminative feature.

        Returns:
            Series of F-scores sorted descending
        """
        print("\n--- Method 2: SelectKBest (f_classif) ---")

        selector = SelectKBest(
            score_func=f_classif,
            k='all'
        )
        selector.fit(self.X, self.y_encoded)

        scores = pd.Series(
            selector.scores_,
            index=self.X.columns
        ).sort_values(ascending=False)

        # Normalize scores to 0-1 for comparison
        scores_norm = scores / scores.max()

        # Save
        scores.to_frame('F_Score').to_csv(
            os.path.join(
                self.output_dir,
                'method2_selectkbest.csv'
            )
        )

        # Plot
        plt.figure(figsize=(12, 6))
        colors = [
            'darkorange' if v > scores.mean() else 'lightgray'
            for v in scores.values
        ]
        plt.bar(
            scores.index,
            scores.values,
            color=colors, edgecolor='black'
        )
        plt.axhline(
            y=scores.mean(), color='red',
            linestyle='--', linewidth=1.5,
            label=f'Mean F-Score = {scores.mean():.2f}'
        )
        plt.title(
            'Method 2: SelectKBest F-Scores',
            fontsize=13
        )
        plt.xlabel('Feature')
        plt.ylabel('F-Score')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'method2_selectkbest.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()

        print("Top features by F-Score:")
        print(scores.head(10).to_string())
        print("Saved: method2_selectkbest.png")

        return scores_norm

    # ─────────────────────────────────────────────────────────────
    def method3_rf_importance(self) -> pd.Series:
        """
        Method 3: Random Forest feature importance.

        Trains a quick RF classifier and extracts
        feature importance scores (mean decrease impurity).

        Returns:
            Series of importance scores sorted descending
        """
        print("\n--- Method 3: Random Forest Importance ---")

        rf = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(self.X, self.y_encoded)

        importance = pd.Series(
            rf.feature_importances_,
            index=self.X.columns
        ).sort_values(ascending=False)

        # Save
        importance.to_frame('RF_Importance').to_csv(
            os.path.join(
                self.output_dir,
                'method3_rf_importance.csv'
            )
        )

        # Plot
        plt.figure(figsize=(12, 6))
        colors = [
            'green' if v > importance.mean() else 'lightgray'
            for v in importance.values
        ]
        plt.bar(
            importance.index,
            importance.values,
            color=colors, edgecolor='black'
        )
        plt.axhline(
            y=importance.mean(), color='red',
            linestyle='--', linewidth=1.5,
            label=f'Mean = {importance.mean():.4f}'
        )
        plt.title(
            'Method 3: Random Forest Feature Importance',
            fontsize=13
        )
        plt.xlabel('Feature')
        plt.ylabel('Importance Score')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'method3_rf_importance.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()

        print("Top features by RF Importance:")
        print(importance.head(10).to_string())
        print("Saved: method3_rf_importance.png")

        return importance

    # ─────────────────────────────────────────────────────────────
    def combine_and_select(
        self,
        corr_scores: pd.Series,
        kbest_scores: pd.Series,
        rf_scores: pd.Series,
        top_n: int = 12
    ) -> list:
        """
        Combine all three methods into one ranking.

        Normalizes each method score to 0-1 then averages.
        Selects top_n features by combined score.

        Args:
            corr_scores  : Correlation scores (normalized)
            kbest_scores : SelectKBest scores (normalized)
            rf_scores    : RF importance scores (normalized)
            top_n        : Number of features to select

        Returns:
            List of selected feature names
        """
        print("\n--- Combining All Methods ---")

        # Normalize all to 0-1
        def normalize(s):
            if s.max() == 0:
                return s
            return s / s.max()

        combined = pd.DataFrame({
            'Correlation' : normalize(corr_scores),
            'SelectKBest' : normalize(kbest_scores),
            'RF_Importance': normalize(rf_scores),
        }).fillna(0)

        combined['Combined_Score'] = combined.mean(axis=1)
        combined = combined.sort_values(
            'Combined_Score', ascending=False
        )

        # Save full comparison
        combined.to_csv(
            os.path.join(
                self.output_dir,
                'feature_selection_combined.csv'
            )
        )

        # Select top N features
        self.selected_features = (
            combined.head(top_n).index.tolist()
        )

        # Plot combined scores
        plt.figure(figsize=(14, 6))

        x = np.arange(len(combined))
        width = 0.25

        plt.bar(
            x - width, combined['Correlation'],
            width, label='Correlation',
            color='steelblue', edgecolor='black',
            alpha=0.8
        )
        plt.bar(
            x, combined['SelectKBest'],
            width, label='SelectKBest',
            color='darkorange', edgecolor='black',
            alpha=0.8
        )
        plt.bar(
            x + width, combined['RF_Importance'],
            width, label='RF Importance',
            color='green', edgecolor='black',
            alpha=0.8
        )

        plt.xticks(
            x, combined.index,
            rotation=45, ha='right', fontsize=9
        )
        plt.title(
            'Feature Selection — Combined Score '
            '(All 3 Methods)',
            fontsize=13
        )
        plt.ylabel('Normalized Score (0-1)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'feature_selection_combined.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: feature_selection_combined.png")

        print(f"\nTop {top_n} Selected Features:")
        for i, feat in enumerate(self.selected_features, 1):
            score = combined.loc[feat, 'Combined_Score']
            print(f"  {i:2}. {feat:<35} Score: {score:.4f}")

        return self.selected_features

    # ─────────────────────────────────────────────────────────────
    def plot_full_correlation_heatmap(self):
        """
        Plot full correlation heatmap of selected features
        for final verification before model training.
        """
        if not self.selected_features:
            print("Run combine_and_select() first.")
            return

        plt.figure(figsize=(14, 10))
        corr = self.X[self.selected_features].corr()
        sns.heatmap(
            corr,
            annot=True, fmt='.2f',
            cmap='coolwarm',
            linewidths=0.5,
            square=True,
            annot_kws={'size': 8}
        )
        plt.title(
            'Correlation Heatmap — Selected Features',
            fontsize=13
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'selected_features_heatmap.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: selected_features_heatmap.png")

    # ─────────────────────────────────────────────────────────────
    def run_feature_selection(self, top_n: int = 12) -> list:
        """
        Run complete feature selection pipeline.

        Args:
            top_n : Number of top features to select

        Returns:
            List of selected feature names
        """
        print("\n" + "="*55)
        print("     STEP 5: FEATURE SELECTION")
        print("="*55)

        self.prepare_X_y()

        corr_scores  = self.method1_correlation()
        kbest_scores = self.method2_selectkbest()
        rf_scores    = self.method3_rf_importance()

        selected = self.combine_and_select(
            corr_scores, kbest_scores, rf_scores,
            top_n=top_n
        )

        self.plot_full_correlation_heatmap()

        print("\n" + "="*55)
        print("Step 5 — Feature Selection COMPLETE!")
        print(f"Selected {len(selected)} features for training.")
        print("="*55)
        # Save selected features for Step 12
        pd.Series(self.selected_features).to_csv(
            './Models/final_features.csv',
            index=False
        )
        print("Saved: ./Models/final_features.csv")
        return selected

    # ─────────────────────────────────────────────────────────────
    def get_selected_features(self) -> list:
        """Return the selected feature list."""
        return self.selected_features

    def get_X_y(self):
        """Return feature matrix and encoded target."""
        return self.X, self.y_encoded

    def get_class_names(self) -> list:
        """Return original class names."""
        return list(self.target_encoder.classes_)