import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score

class CrossValidator:
    def __init__(self, model, model_name, X, y, n_splits=5, random_state=42):
        self.model = model
        self.model_name = model_name
        self.X = X.reset_index(drop=True)
        self.y = y.reset_index(drop=True)
        self.n_splits = n_splits
        self.random_state = random_state
        self.results_ = None

    def _print_header(self):
        print("\n" + "="*55)
        print("     STEP 9: CROSS-VALIDATION")
        print("="*55)
        print(f"Model    : {self.model_name}")
        print(f"Samples  : {len(self.X)}")
        print(f"Folds    : {self.n_splits}-Fold Stratified")

    def run(self, save_path="cv_results.csv"):
        self._print_header()

        skf = StratifiedKFold(
            n_splits=self.n_splits,
            shuffle=True,
            random_state=self.random_state
        )

        rows = []

        for i, (tr, te) in enumerate(skf.split(self.X, self.y), start=1):
            X_tr, X_te = self.X.iloc[tr], self.X.iloc[te]
            y_tr, y_te = self.y.iloc[tr], self.y.iloc[te]

            model = self.model
            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)

            acc = accuracy_score(y_te, y_pred)
            f1w = f1_score(y_te, y_pred, average="weighted")

            rows.append({"Fold": i, "Accuracy": acc, "F1_weighted": f1w})
            print(f"Fold {i:>2}: Accuracy={acc:.4f} | F1_w={f1w:.4f}")

        df = pd.DataFrame(rows)
        self.results_ = df

        print("\n===== CV SUMMARY =====")
        print(f"Mean Accuracy : {df['Accuracy'].mean():.4f}")
        print(f"Std  Accuracy : {df['Accuracy'].std():.4f}")
        print(f"Mean F1_w     : {df['F1_weighted'].mean():.4f}")
        print(f"Std  F1_w     : {df['F1_weighted'].std():.4f}")

        df.to_csv(save_path, index=False)
        print(f"Saved: {save_path}")

        return df