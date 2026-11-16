import pandas as pd
import numpy as np

class DataSampler:
    def __init__(self, X, y, random_state=42):

        # Handle X
        if isinstance(X, pd.DataFrame):
            self.X = X.reset_index(drop=True)
        else:
            self.X = pd.DataFrame(X).reset_index(drop=True)

        # Handle y
        if isinstance(y, pd.Series):
            self.y = y.reset_index(drop=True)
        else:
            self.y = pd.Series(y).reset_index(drop=True)

        self.random_state = random_state

    def _print_header(self):
        print("\n" + "="*55)
        print("     STEP 8: DATA SAMPLING")
        print("="*55)

    def _class_distribution(self, y):
        dist = y.value_counts(normalize=False).sort_index()
        pct = (dist / len(y) * 100).round(2)
        df = pd.DataFrame({"Count": dist, "Percent": pct})
        return df

    def get_sample(self, n_samples=500, stratified=True):
        self._print_header()

        n = len(self.X)
        n_samples = min(n_samples, n)

        print(f"Total rows     : {n}")
        print(f"Requested size : {n_samples}")
        print(f"Stratified     : {stratified}")

        if stratified:
            # proportional stratified sampling
            df = self.X.copy()
            df["_y"] = self.y

            parts = []
            rng = np.random.RandomState(self.random_state)
            for cls, group in df.groupby("_y"):
                k = max(1, int(round(len(group) / n * n_samples)))
                idx = rng.choice(group.index, size=min(k, len(group)), replace=False)
                parts.append(group.loc[idx])

            sampled = pd.concat(parts).sample(frac=1, random_state=self.random_state)
            X_s = sampled.drop(columns=["_y"]).reset_index(drop=True)
            y_s = sampled["_y"].reset_index(drop=True)
        else:
            rng = np.random.RandomState(self.random_state)
            idx = rng.choice(n, size=n_samples, replace=False)
            X_s = self.X.iloc[idx].reset_index(drop=True)
            y_s = self.y.iloc[idx].reset_index(drop=True)

        print("\nClass distribution (original):")
        print(self._class_distribution(self.y))
        print("\nClass distribution (sample):")
        print(self._class_distribution(y_s))

        return X_s, y_s