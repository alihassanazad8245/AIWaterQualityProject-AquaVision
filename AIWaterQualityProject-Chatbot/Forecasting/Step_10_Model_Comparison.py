import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# compares models using metrics
class ModelComparator:

    METRICS = ["RMSE", "MAE", "MAPE"]

    # initializes comparator
    def __init__(self, output_dir: str = "./ModelComparison"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # compares models and generates charts
    def compare_models(self, results: list) -> pd.DataFrame:
        df = pd.DataFrame(results).sort_values("RMSE").reset_index(drop=True)
        df.to_csv(os.path.join(self.output_dir, "model_comparison.csv"), index=False)

        for metric in self.METRICS:
            if metric not in df.columns:
                continue
            fig, ax = plt.subplots(figsize=(10, 5))
            palette = sns.color_palette("Set2", n_colors=len(df))
            bars    = ax.bar(df["Model"], df[metric], color=palette)
            for bar, val in zip(bars, df[metric]):
                if not np.isnan(val):
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.005 * abs(bar.get_height()),
                            f"{val:.3f}", ha="center", fontsize=9)
            ax.set_title(f"{metric} — Model Comparison", fontsize=13)
            ax.set_ylabel(metric); ax.set_xlabel("Model")
            ax.tick_params(axis="x", rotation=20)
            ax.grid(axis="y", alpha=0.3)
            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, f"comparison_{metric}.png"),
                dpi=150,
            )
            plt.close()

        self._grouped_bar(df)
        self._radar_chart(df)

        return df

    # creates grouped bar chart
    def _grouped_bar(self, df: pd.DataFrame):
        available = [m for m in self.METRICS if m in df.columns]
        if not available:
            return

        x     = np.arange(len(df))
        width = 0.25
        colors = ["steelblue", "tomato", "green"]

        fig, ax = plt.subplots(figsize=(12, 5))
        for i, (metric, color) in enumerate(zip(available, colors)):
            vals = df[metric].values.astype(float)
            ax.bar(x + i * width, vals, width=width,
                   label=metric, color=color, alpha=0.85)
            for j, v in enumerate(vals):
                if not np.isnan(v):
                    ax.text(x[j] + i * width, v + 0.005 * abs(v),
                            f"{v:.2f}", ha="center", fontsize=7.5)

        ax.set_xticks(x + width)
        ax.set_xticklabels(df["Model"], rotation=15)
        ax.set_title("All Models — MAE / RMSE / MAPE Comparison", fontsize=13)
        ax.legend(); ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, "comparison_grouped.png"), dpi=150
        )
        plt.close()

    # creates radar chart
    def _radar_chart(self, df: pd.DataFrame):
        metrics   = [m for m in self.METRICS if m in df.columns]
        n_metrics = len(metrics)
        n_models  = len(df)
        if n_metrics < 2 or n_models < 2:
            return

        norm = df[metrics].copy().astype(float)
        for m in metrics:
            col_min, col_max = norm[m].min(), norm[m].max()
            norm[m] = (
                (norm[m] - col_min) / (col_max - col_min)
                if col_max > col_min else 0.0
            )

        angles  = [i / n_metrics * 2 * np.pi for i in range(n_metrics)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        palette = plt.cm.Set2(np.linspace(0, 1, n_models))

        for idx, row in df.iterrows():
            vals = [norm.loc[idx, m] for m in metrics]
            vals += vals[:1]
            ax.plot(angles, vals, label=row["Model"],
                    color=palette[idx], linewidth=1.8)
            ax.fill(angles, vals, alpha=0.08, color=palette[idx])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=12)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7)
        ax.set_title(
            "Normalised Metric Comparison\n(lower = better for all axes)",
            fontsize=12, pad=25,
        )
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15), fontsize=9)
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, "radar_comparison.png"), dpi=150
        )
        plt.close()

    # prints leaderboard
    def print_leaderboard(self, df: pd.DataFrame):
        if df.empty:
            return
        print("\n" + "═" * 52)
        print("  MODEL LEADERBOARD  (sorted by RMSE ↑)")
        print("═" * 52)
        for rank, row in df.iterrows():
            print(f"  {rank + 1}.  {row['Model']:<18s}  "
                  f"RMSE={row['RMSE']:.4f}  "
                  f"MAE={row['MAE']:.4f}  "
                  f"MAPE={row['MAPE']:.2f}%")
        best = df.iloc[0]
        print("─" * 52)
        print(f"BEST : {best['Model']}")
        print("═" * 52 + "\n")