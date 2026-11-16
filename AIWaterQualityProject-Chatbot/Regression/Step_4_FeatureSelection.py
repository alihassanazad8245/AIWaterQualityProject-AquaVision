import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from sklearn.preprocessing import OneHotEncoder

class FeatureSelection:
    def __init__(self, transformed_df, target_col='WQI', output_dir="./FeatureSelection"):
        self.df = transformed_df.copy()
        self.target_col = target_col
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.corr_target = None
        self.selected_features = None

    # 1. Correlation Heatmap
    def corr_heatmap(self, idx_s=0, idx_e=None):
        if idx_e is None:
            idx_e = len(self.df.columns) - 1

        plt.figure(figsize=(22, 10))
        y = self.df[self.target_col]
        temp = self.df.iloc[:, idx_s:idx_e].copy()
        if 'Sample ID' in temp.columns:
            temp = temp.drop('Sample ID', axis=1)
        temp[self.target_col] = y
        # Select only numeric columns before correlation
        numeric_temp = temp.select_dtypes(include=[np.number])
        if numeric_temp.shape[1] > 1:
            sns.heatmap(numeric_temp.corr(), annot=True, fmt='.2f', cmap='viridis')
        plt.title('Heat Map of Correlation Matrix of Water Quality Data', fontsize=22)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "fullcorrelationgraph.png"))
        plt.show()

    # 2. Compute Correlation with Target
    def compute_correlation(self):
        target_df = self.df.copy()
        # Encode target column if not numeric
        if not pd.api.types.is_numeric_dtype(target_df[self.target_col]):
            ohe = OneHotEncoder()
            target_df[self.target_col] = ohe.fit_transform(target_df[self.target_col])

        target_df = target_df.select_dtypes(include=[np.number])
        corrmat = target_df.corr()
        self.corr_target = abs(corrmat[self.target_col])
        self.corr_target.to_csv(os.path.join(self.output_dir, "cor_targetfeatures.csv"))

        # Barplot of correlations
        plt.figure(figsize=(22, 10))
        cor_sorted = self.corr_target.sort_values(ascending=False).dropna()
        cor_sorted.plot.bar()
        plt.title(f'Top Most Correlated Features with {self.target_col}', fontsize=22)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "correlationgraph.png"))
        plt.show()

        return self.corr_target

    # 3. Select Features based on Correlation Threshold
    def select_features(self, threshold=0.1, drop_cols=None):
        if self.corr_target is None:
            raise ValueError("Run compute_correlation() first.")

        if drop_cols is None:
            drop_cols = ['Error', 'WQI', 'Water Quality Class', 'Sample ID',
                         'Sample Date', 'Reference']

        # Filter features above threshold and exclude unwanted columns
        filtered               = self.corr_target[~self.corr_target.index.isin(drop_cols)]
        self.selected_features = filtered[filtered > threshold].sort_values(ascending=False).index.tolist()

        # Save selected features with scores
        most_corr = pd.DataFrame({
            "Most Correlated Features": self.selected_features,
            "Score" : filtered[self.selected_features].values
        })
        most_corr.to_csv(os.path.join(self.output_dir, "mostcorrelatedfeatures.csv"), index=False)

        print(f"Selected Features (corr > {threshold}):")
        print(self.selected_features)

        # Return DataFrame with selected features AND target column
        df_selected = self.df[self.selected_features + [self.target_col]]
        return df_selected

    # 4. Run Feature Selection
    def run_feature_selection(self, idx_s=0, idx_e=None, threshold=0.02, drop_cols=None):
        self.corr_heatmap(idx_s=idx_s, idx_e=idx_e)
        self.compute_correlation()
        df_selected = self.select_features(threshold=threshold, drop_cols=drop_cols)
        print("\n Feature Selection completed successfully.")
        return df_selected, self.selected_features