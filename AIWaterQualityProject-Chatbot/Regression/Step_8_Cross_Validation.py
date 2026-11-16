import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.exceptions import UndefinedMetricWarning
import warnings


class LogoCrossValidation:
    def __init__(self, X, y, model, model_name=None, n_splits=5):
        self.X = X
        self.y = y
        self.model = model
        self.model_name = model_name if model_name else type(model).__name__
        self.n_splits = n_splits
        self.results = []

    # K-Fold cross-validation
    def run_logo_cv(self):
        self.results = []
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)

        for fold, (train_idx, test_idx) in enumerate(kf.split(self.X), start=1):
            X_train = self.X.iloc[train_idx]
            X_test  = self.X.iloc[test_idx]
            y_train = self.y.iloc[train_idx]
            y_test  = self.y.iloc[test_idx]

            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)

            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
                    r2 = r2_score(y_test, y_pred)
            except Exception:
                r2 = np.nan

            self.results.append({
                "Fold": fold,
                "RMSE": rmse,
                "R2":   r2,
            })

            print(f"  Fold {fold:2d} | RMSE: {rmse:.2f} | R2: {r2:.2f}")

        return pd.DataFrame(self.results)

    # Summary statistics
    def summary(self):
        if not self.results:
            raise ValueError("Run run_logo_cv() first.")

        results_df = pd.DataFrame(self.results)

        print("\n K-FOLD CV SUMMARY ")
        print(f"Model: {self.model_name}")
        print(f"\nAvg RMSE : {results_df['RMSE'].mean():.4f}")
        print(f"Avg R2 : {results_df['R2'].mean():.4f}")
        print(f"\n  Std RMSE : {results_df['RMSE'].std():.4f}")
        print(f"Std R2 : {results_df['R2'].std():.4f}")

        return results_df