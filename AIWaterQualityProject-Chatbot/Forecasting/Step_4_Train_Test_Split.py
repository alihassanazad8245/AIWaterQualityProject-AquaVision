import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit


# handles chronological train test splitting
class TrainTestSplitter:

    # initializes the splitter
    def __init__(self, series, test_size = 0.2, n_splits  = 5, output_dir = "./DataSplit"):
        if not isinstance(series.index, pd.DatetimeIndex):
            raise TypeError("series must have a DatetimeIndex.")

        self.series = series.sort_index()
        self.test_size = test_size
        self.n_splits = n_splits
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.train: pd.Series = None
        self.test:  pd.Series = None

    # performs chronological split
    def split(self) -> tuple:
        n = len(self.series)
        if n < 2:
            raise ValueError(
                f"Cannot split a series with only {n} period(s) into train/test. "
                f"Need at least 2 — check upstream resampling/date parsing."
            )

        split = int(n * (1 - self.test_size))
        split = max(1, min(split, n - 1))  # guarantee both sides non-empty

        self.train = self.series.iloc[:split]
        self.test = self.series.iloc[split:]

        if len(self.train) == 0 or len(self.test) == 0:
            raise ValueError(
                f"Train/test split produced an empty split (n_train={len(self.train)}, "
                f"n_test={len(self.test)}) from {n} total periods and "
                f"test_size={self.test_size}. Provide more data or adjust test_size."
            )

        print(f"Train: {len(self.train):4d} periods  "
              f"[{self.train.index[0].date()} to {self.train.index[-1].date()}]")
        print(f"Test : {len(self.test):4d}  periods  "
              f"[{self.test.index[0].date()} to {self.test.index[-1].date()}]")

        self._save_summary()
        self._plot_split()
        return self.train, self.test

    # returns walk forward splits
    def walk_forward_splits(self) -> TimeSeriesSplit:
        return TimeSeriesSplit(n_splits=self.n_splits)

    # plots train test split
    def _plot_split(self):
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.plot(self.train.index, self.train.values,
                color="steelblue", linewidth=1.5, label="Train")
        ax.plot(self.test.index, self.test.values,
                color="tomato", linewidth=1.5, label="Test")
        ax.axvline(self.test.index[0], color="gray",
                   linestyle="--", linewidth=2, label="Split point")
        ax.set_title("Chronological Train / Test Split — Risk_Score", fontsize=13)
        ax.set_xlabel("Date"); ax.set_ylabel("Risk_Score")
        ax.legend(); ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "train_test_split.png"), dpi=150)
        plt.close()
        print(f"Split plot saved.")

    # saves summary csv
    def _save_summary(self):
        pd.DataFrame([{
            "train_start": str(self.train.index[0].date()),
            "train_end":   str(self.train.index[-1].date()),
            "test_start":  str(self.test.index[0].date()),
            "test_end":    str(self.test.index[-1].date()),
            "n_train":     len(self.train),
            "n_test":      len(self.test),
        }]).to_csv(
            os.path.join(self.output_dir, "split_summary.csv"), index=False
        )

    # runs full split pipeline
    def run_split(self):
        print("\nTrain-Test Split")
        train, test = self.split()
        print(" Train-Test Split completed.\n")
        return train, test