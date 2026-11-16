import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, r2_score
import os

class ModelEvaluator:
    def __init__(self, X_test, y_test, model, model_name, output_dir="./ModelTraining"):
        self.X_test = X_test
        self.y_test = y_test
        self.model = model
        self.model_name = model_name
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.metrics_df = None

    # 1. Predict & evaluate basic metrics
    def evaluate_model(self):
        y_pred = self.model.predict(self.X_test)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        mae = np.mean(np.abs(self.y_test - y_pred))
        r2 = r2_score(self.y_test, y_pred)

        print(f"\n{self.model_name} Test Set Performance:")
        print(f"RMSE : {rmse:.4f}")
        print(f"MAE : {mae:.4f}")
        print(f"R² Score: {r2:.4f}")

        self.metrics_df = pd.DataFrame({
            'Model' : [self.model_name],
            'RMSE' : [rmse],
            'MAE' : [mae],
            'R2_Score': [r2]
        })
        return y_pred

    # 2. Scatter plot: Actual vs Predicted WQI
    def plot_scatter_with_margin(self, y_pred):
        y_test = np.array(self.y_test)
        y_pred = np.array(y_pred)

        plt.figure(figsize=(12, 6))
        sns.scatterplot(x=y_test, y=y_pred, alpha=0.6)

        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        plt.plot([min_val, max_val], [min_val, max_val], color='red', linestyle='--', linewidth=2, label='Perfect Prediction')

        plt.xlabel("y_test (Actual) WQI")
        plt.ylabel("y_pred (Predicted) WQI")
        plt.title(f"{self.model_name} Actual vs Predicted WQI", fontsize=14)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f"{self.model_name.replace(' ', '_')}_scatterplot.png"))
        plt.show()
        plt.close()

    # 3. Run full evaluation
    def run_full_evaluation(self):
        y_pred = self.evaluate_model()
        self.plot_scatter_with_margin(y_pred)
        print(f"\n {self.model_name} Evaluation Completed Successfully.")
        return self.metrics_df