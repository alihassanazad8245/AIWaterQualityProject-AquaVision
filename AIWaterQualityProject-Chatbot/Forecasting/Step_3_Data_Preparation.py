import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler


# prepares data for statistical models and lstm
class DataPreparation:

    # initializes the class
    def __init__(self, ts_df, target_col = "Risk_Score", look_back = 12, output_dir = "./DataPreparation"):
        if not isinstance(ts_df.index, pd.DatetimeIndex):
            raise TypeError("ts_df must have a DatetimeIndex.")

        self.ts_df = ts_df.copy()
        self.target_col = target_col
        self.look_back  = look_back
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.series : pd.Series = None
        self.scaler : MinMaxScaler = None
        self.scaled : np.ndarray = None

    # extracts clean target series
    def extract_series(self):
        self.series = (self.ts_df[self.target_col].ffill().bfill())
        if self.series.isna().any():
            raise ValueError("Risk_Score series still contains NaN after ffill/bfill.")
        print(f"Target series: {len(self.series)} periods "
              f"[{self.series.index[0].date()} → {self.series.index[-1].date()}]")
        return self.series

    # scales the series using minmax
    def scale_series(self) -> np.ndarray:
        values = self.series.values.reshape(-1, 1)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaled = self.scaler.fit_transform(values)
        print(f"Scaled range: [{self.scaled.min():.4f}, {self.scaled.max():.4f}]")
        return self.scaled

    # creates lstm sequences
    @staticmethod
    def create_sequences(data, look_back):
        data = data.flatten()
        X, y = [], []
        for i in range(look_back, len(data)):
            X.append(data[i - look_back : i])
            y.append(data[i])
        X = np.array(X).reshape(-1, look_back, 1)
        y = np.array(y)
        return X, y

    # splits sequences into train and test
    def split_sequences(self, X: np.ndarray, y: np.ndarray, test_size= 0.2):
        split = int(len(X) * (1 - test_size))
        return X[:split], X[split:], y[:split], y[split:]

    # gets datetime index for test predictions
    def get_test_index(self, test_size = 0.2):
        split = int(len(self.series) * (1 - test_size))
        return self.series.index[split + self.look_back:]

    # plots scaled and original series
    def _plot_scaled(self):
        fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
        axes[0].plot(self.series.index, self.series.values,
                     color="steelblue", linewidth=1.5)
        axes[0].set_title("Original Risk_Score Series", fontsize=11)
        axes[0].grid(alpha=0.3)

        axes[1].plot(self.series.index, self.scaled.flatten(),
                     color="darkorange", linewidth=1.5)
        axes[1].set_title("Scaled Risk_Score Series  [0, 1]  (MinMaxScaler)", fontsize=11)
        axes[1].grid(alpha=0.3)

        plt.suptitle("Risk_Score — Original vs Scaled", fontsize=13)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "Risk_Score_scaled.png"), dpi=150)
        plt.close()

    # runs full data preparation pipeline
    def run_preparation(self, test_size = 0.2):
        print("\nData Preparation")
        self.extract_series()
        self.scale_series()
        self._plot_scaled()

        X, y = self.create_sequences(self.scaled, self.look_back)
        X_train, X_test, y_train, y_test = self.split_sequences(X, y, test_size=test_size)

        test_index = self.get_test_index(test_size=test_size)

        print(f"look_back : {self.look_back}")
        print(f"LSTM train : {X_train.shape[0]} sequences")
        print(f"LSTM test : {X_test.shape[0]}  sequences")
        print("Data Preparation completed.\n")

        return {
            "series":      self.series,
            "scaler":      self.scaler,
            "scaled":      self.scaled,
            "X_train_seq": X_train,
            "X_test_seq":  X_test,
            "y_train_seq": y_train,
            "y_test_seq":  y_test,
            "test_index":  test_index,
            "look_back":   self.look_back,
        }