import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class ModelComparator:
    def __init__(self, output_dir="./ModelComparison"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _to_df(metrics):
        if isinstance(metrics, dict):
            return pd.DataFrame([metrics])
        return metrics

    def compare_multiple_models(self, models):
        rows = []
        for name, metrics_df in models:
            metrics_df = self._to_df(metrics_df)
            rows.append({
                "Model": name,
                "RMSE": metrics_df["RMSE"].values[0],
                "MAE": metrics_df["MAE"].values[0],
                "R2_Score": metrics_df["R2_Score"].values[0],
            })
        comparison_df = pd.DataFrame(rows)


        # Bar chart per metric
        for metric in ["RMSE", "MAE", "R2_Score"]:
            plt.figure(figsize=(9, 5))
            sns.barplot(data=comparison_df, x="Model", y=metric, hue="Model", palette="Set2", legend=False)
            plt.title(f"{metric} — All Models")
            plt.ylabel(metric)
            plt.xlabel("Model")
            plt.xticks(rotation=15)
            for i, val in enumerate(comparison_df[metric]):
                plt.text(i, val + 0.01 * abs(val), f"{val:.4f}", ha='center', fontsize=9)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, f"MultiModel_{metric}.png"))
            plt.show()
            plt.close()

        return comparison_df