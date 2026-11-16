import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    matthews_corrcoef,
    cohen_kappa_score,
    classification_report,
    confusion_matrix
)

class ModelComparator:
    def __init__(self, models_dict, X_test, y_test):
        """
        models_dict = {
            "Random Forest": rf_model,
            "Gradient Boosting": gb_model,
            "Decision Tree": dt_model,
            "SVM": svm_model,
            "GB (Tuned)": best_model
        }
        """
        self.models = models_dict
        self.X_test = X_test
        self.y_test = y_test
        self.results_ = None

        # Ensure Models folder exists
        os.makedirs('./Models', exist_ok=True)

    def _print_header(self):
        print("\n" + "="*70)
        print("     STEP 11: FINAL MODEL COMPARISON")
        print("="*70)

    def evaluate_all(self, save_path="final_model_results.csv"):
        self._print_header()

        rows = []

        for name, model in self.models.items():
            y_pred = model.predict(self.X_test)

            accuracy = accuracy_score(self.y_test, y_pred)
            balanced_acc = balanced_accuracy_score(self.y_test, y_pred)

            precision_macro = precision_score(self.y_test, y_pred, average='macro', zero_division=0)
            precision_weighted = precision_score(self.y_test, y_pred, average='weighted', zero_division=0)

            recall_macro = recall_score(self.y_test, y_pred, average='macro', zero_division=0)
            recall_weighted = recall_score(self.y_test, y_pred, average='weighted', zero_division=0)

            f1_macro = f1_score(self.y_test, y_pred, average='macro', zero_division=0)
            f1_weighted = f1_score(self.y_test, y_pred, average='weighted', zero_division=0)

            mcc = matthews_corrcoef(self.y_test, y_pred)
            kappa = cohen_kappa_score(self.y_test, y_pred)

            rows.append({
                "Model": name,
                "Accuracy": accuracy,
                "Balanced Accuracy": balanced_acc,
                "Precision (Macro)": precision_macro,
                "Precision (Weighted)": precision_weighted,
                "Recall (Macro)": recall_macro,
                "Recall (Weighted)": recall_weighted,
                "F1 (Macro)": f1_macro,
                "F1 (Weighted)": f1_weighted,
                "MCC": mcc,
                "Cohen Kappa": kappa
            })

            print(f"\n{name}")
            print("-" * 60)
            print(f"Accuracy            : {accuracy:.4f}")
            print(f"Balanced Accuracy   : {balanced_acc:.4f}")
            print(f"Precision (Macro)   : {precision_macro:.4f}")
            print(f"Precision (Weighted): {precision_weighted:.4f}")
            print(f"Recall (Macro)      : {recall_macro:.4f}")
            print(f"Recall (Weighted)   : {recall_weighted:.4f}")
            print(f"F1 (Macro)          : {f1_macro:.4f}")
            print(f"F1 (Weighted)       : {f1_weighted:.4f}")
            print(f"MCC                 : {mcc:.4f}")
            print(f"Cohen's Kappa       : {kappa:.4f}")

            print("\nClassification Report:")
            print(classification_report(self.y_test, y_pred, zero_division=0))

            cm = confusion_matrix(self.y_test, y_pred)

            plt.figure(figsize=(6, 5))
            sns.heatmap(cm,
                        annot=True,
                        fmt='d',
                        cmap='Blues',
                        cbar=False)

            plt.title(f"Confusion Matrix - {name}")
            plt.xlabel("Predicted")
            plt.ylabel("Actual")
            plt.tight_layout()
            plt.savefig(f'./Models/{name}_confusion_matrix.png', dpi=300)
            plt.show()
            plt.close()

        # Create results dataframe
        df = pd.DataFrame(rows)

        df = df.sort_values(
            by=["F1 (Weighted)", "Accuracy"],
            ascending=False
        )
        self.results_ = df

        print("\n===== FINAL RANKING =====")
        print(df)

        # Save CSV
        df.to_csv(save_path, index=False)
        print(f"Saved: {save_path}")

        #  SAVE FINAL MODEL (BEST ONE)
        best_model_name = "GB (Tuned)"
        best_model = self.models[best_model_name]

        joblib.dump(best_model, './Models/final_model.pkl')
        print(f"\nFinal model saved: {best_model_name} → final_model.pkl")

        return df