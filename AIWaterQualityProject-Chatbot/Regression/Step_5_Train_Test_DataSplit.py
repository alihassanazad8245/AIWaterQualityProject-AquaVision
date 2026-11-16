import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

class DataSplitter:
    def __init__(self, df_selected, df, selected_features, random_state=42):
        self.df_selected = df_selected.copy()
        self.df = df.copy()
        self.selected_features = selected_features
        self.random_state = random_state

        # Outputs
        self.X = None
        self.y = None
        self.groups = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.test_group = None

    # 1. Prepare features, target, and groups
    def prepare_features_target_groups(self):
        # Remove non-predictive columns
        drop_cols    = ['WQI', 'Water Quality Class', 'Sample ID', 'Sample Date', 'Reference']
        feature_cols = [f for f in self.selected_features if f not in drop_cols]

        self.X = self.df_selected[feature_cols]
        self.y = self.df.loc[self.X.index, 'WQI']
        self.groups = self.df.loc[self.X.index, 'City']

        return self.X, self.y, self.groups

    # 2. Stratified 80/20 split, stratify on Water Quality Class so every
    def split_train_test(self, test_size=0.2):
        # Stratification column, WQI class
        stratify_col = self.df.loc[self.X.index, 'Water Quality Class']

        (self.X_train, self.X_test,
         self.y_train, self.y_test) = train_test_split(
            self.X, self.y,
            test_size = test_size,
            random_state = self.random_state,
            stratify = stratify_col
        )

        # Print class distribution to confirm balance
        train_dist = self.df.loc[self.X_train.index, 'Water Quality Class'].value_counts(normalize=True)
        test_dist  = self.df.loc[self.X_test.index,  'Water Quality Class'].value_counts(normalize=True)
        print("\nWQI class proportions — train vs test:")
        dist_df = pd.DataFrame({'Train %': (train_dist * 100).round(1), 'Test %':  (test_dist  * 100).round(1)}).fillna(0)
        print(dist_df.to_string())

        print("\nX_train shape:", self.X_train.shape)
        print("X_test shape: ", self.X_test.shape)
        print("y_train shape:", self.y_train.shape)
        print("y_test shape: ", self.y_test.shape)

        return (
            self.X_train,
            self.X_test,
            self.y_train,
            self.y_test,
            self.groups,
            self.test_group
        )

    # 3. Run full split
    def run_split(self):
        self.prepare_features_target_groups()
        return self.split_train_test()