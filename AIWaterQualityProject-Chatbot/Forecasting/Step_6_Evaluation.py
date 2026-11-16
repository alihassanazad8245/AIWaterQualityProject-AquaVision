import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


# evaluates time series models
class TimeSeriesEvaluator:

    # initializes evaluator
    def __init__(
        self,
        model_name,
        output_dir = "./Evaluation",
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.metrics: dict = {}

    # generates file path
    def _fp(self, name: str) -> str:
        prefix = self.model_name.replace(" ", "_")
        return os.path.join(self.output_dir, f"{prefix}_{name}")

    # saves plot
    def _save(self, name: str):
        plt.tight_layout()
        plt.savefig(self._fp(name), dpi=150, bbox_inches="tight")
        plt.close()

    # computes evaluation metrics
    def compute_metrics(self, y_true, y_pred) -> dict:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        mae  = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

        mask = y_true != 0
        mape = (
            float(np.mean(
                np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])
            ) * 100)
            if mask.sum() > 0 else float("nan")
        )

        self.metrics = {
            "Model": self.model_name,
            "MAE":   round(mae,  4),
            "RMSE":  round(rmse, 4),
            "MAPE":  round(mape, 2) if not np.isnan(mape) else float("nan"),
        }

        print(f"\n  {self.model_name} — Test-Set Metrics")
        print(f"    MAE  = {mae:.4f}")
        print(f"    RMSE = {rmse:.4f}")
        print(f"    MAPE = {mape:.2f} %")
        return self.metrics

    # plots forecast vs actual
    def plot_forecast(
        self,
        y_true,
        y_pred,
        train_series=None,
        conf_lower=None,
        conf_upper=None,
        index=None,
    ):
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        x_axis = index if index is not None else np.arange(len(y_true))

        fig, ax = plt.subplots(figsize=(14, 5))

        if train_series is not None:
            tx = (train_series.index
                  if hasattr(train_series, "index") else
                  np.arange(len(train_series)))
            ax.plot(tx, np.asarray(train_series),
                    color="steelblue", alpha=0.5, linewidth=1.2,
                    label="Train (actual)")

        ax.plot(x_axis, y_true, color="black",
                linewidth=1.8, label="Test (actual)")
        ax.plot(x_axis, y_pred, color="tomato", linewidth=1.8,
                linestyle="--", label="Forecast")

        if conf_lower is not None and conf_upper is not None:
            ax.fill_between(x_axis,
                            np.asarray(conf_lower),
                            np.asarray(conf_upper),
                            alpha=0.15, color="tomato", label="95 % CI")

        ax.set_title(f"{self.model_name} — Forecast vs Actual", fontsize=13)
        ax.set_xlabel("Date"); ax.set_ylabel("Risk_Score")
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
        self._save("01_forecast.png")

    # plots residuals
    def plot_residuals(self, y_true, y_pred, index=None):
        residuals = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
        x_axis    = index if index is not None else np.arange(len(residuals))

        fig, axes = plt.subplots(1, 2, figsize=(14, 4))

        axes[0].plot(x_axis, residuals, color="steelblue", linewidth=1.2)
        axes[0].axhline(0, color="red", linestyle="--", linewidth=1.5)
        axes[0].set_title("Residuals over Time", fontsize=11)
        axes[0].set_xlabel("Date"); axes[0].set_ylabel("Residual")
        axes[0].grid(alpha=0.3)

        axes[1].hist(residuals, bins=20, color="steelblue",
                     edgecolor="white", alpha=0.85)
        axes[1].axvline(0, color="red", linestyle="--", linewidth=1.5)
        axes[1].set_title("Residual Distribution", fontsize=11)
        axes[1].set_xlabel("Residual")

        plt.suptitle(f"{self.model_name} — Residual Analysis", fontsize=13)
        self._save("02_residuals.png")

    # plots qq plot
    def plot_qq(self, y_true, y_pred):
        residuals = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
        fig, ax = plt.subplots(figsize=(6, 5))
        stats.probplot(residuals, dist="norm", plot=ax)
        ax.set_title(f"{self.model_name} — QQ Plot of Residuals", fontsize=12)
        ax.grid(alpha=0.3)
        self._save("03_qq_plot.png")

    # plots cumulative error
    def plot_cumulative_error(self, y_true, y_pred, index=None):
        residuals  = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
        cumulative = np.cumsum(np.abs(residuals))
        x_axis = index if index is not None else np.arange(len(residuals))

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(x_axis, cumulative, color="darkorange", linewidth=1.8)
        ax.set_title(f"{self.model_name} — Cumulative Absolute Error", fontsize=12)
        ax.set_xlabel("Date"); ax.set_ylabel("Cumulative |Error|")
        ax.grid(alpha=0.3)
        self._save("04_cumulative_error.png")

    # runs full evaluation pipeline
    def run_full_evaluation(
        self,
        y_true,
        y_pred,
        train_series=None,
        conf_lower=None,
        conf_upper=None,
        index=None,
    ) -> dict:
        metrics = self.compute_metrics(y_true, y_pred)
        self.plot_forecast(
            y_true, y_pred,
            train_series=train_series,
            conf_lower=conf_lower,
            conf_upper=conf_upper,
            index=index,
        )
        self.plot_residuals(y_true, y_pred, index=index)
        self.plot_qq(y_true, y_pred)
        self.plot_cumulative_error(y_true, y_pred, index=index)
        print(f"{self.model_name} evaluation complete.")
        return metrics