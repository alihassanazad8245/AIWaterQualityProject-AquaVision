"""
Step_7_ModelTraining.py

Trains multiple classification models on the
water quality dataset with:
    - SMOTE oversampling to fix class imbalance
    - class_weight='balanced' for all models
    - 4 models: Random Forest, Gradient Boosting,
                Decision Tree, SVM
    - Saves all trained models to disk
    - Evaluates all models with full metrics
    - Saves all plots and results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)
from imblearn.over_sampling import SMOTE


class ModelTraining:
    """
    Trains and evaluates multiple classification models
    for water quality prediction.

    Models trained:
        1. Random Forest       - ensemble of decision trees
        2. Gradient Boosting   - sequential boosting model
        3. Decision Tree       - single interpretable tree
        4. SVM                 - support vector classifier

    Imbalance fix:
        SMOTE applied to training set only
        (never applied to test set)

    Overfitting prevention:
        - class_weight='balanced' where supported
        - max_depth limits
        - min_samples_leaf limits
        - Compared train vs test accuracy

    Attributes:
        X_train, X_test  : Feature arrays
        y_train, y_test  : Target arrays
        class_names      : List of class label names
        output_dir       : Folder for saving outputs
        models           : Dict of trained models
        results          : Dict of evaluation metrics
    """

    def __init__(
        self,
        X_train, X_test,
        y_train, y_test,
        class_names: list,
        output_dir: str = './ModelTraining'
    ):
        """
        Initialize ModelTraining.

        Args:
            X_train, X_test : Feature matrices
            y_train, y_test : Target label arrays
            class_names     : Original class name list
            output_dir      : Folder to save all outputs
        """
        self.X_train     = X_train
        self.X_test      = X_test
        self.y_train     = y_train
        self.y_test      = y_test
        self.class_names = class_names
        self.output_dir  = output_dir

        self.models  = {}
        self.results = {}

        self.X_train_smote = None
        self.y_train_smote = None

        os.makedirs(self.output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────
    def apply_smote(self):
        """
        Apply SMOTE to balance training set classes.

        SMOTE creates synthetic samples for minority
        classes by interpolating between existing samples.

        Applied ONLY to training data.
        Test data is NEVER touched.

        Why not just duplicate samples?
            Duplication causes overfitting on exact copies.
            SMOTE creates new realistic synthetic samples.
        """
        print("\nApplying SMOTE to training set...")
        print("Class distribution BEFORE SMOTE:")

        unique, counts = np.unique(
            self.y_train, return_counts=True
        )
        for cls_id, cnt in zip(unique, counts):
            print(f"  {self.class_names[cls_id]:<25} {cnt}")

        smote = SMOTE(random_state=42, k_neighbors=2)
        self.X_train_smote, self.y_train_smote = (
            smote.fit_resample(self.X_train, self.y_train)
        )

        print("\nClass distribution AFTER SMOTE:")
        unique2, counts2 = np.unique(
            self.y_train_smote, return_counts=True
        )
        for cls_id, cnt in zip(unique2, counts2):
            print(f"  {self.class_names[cls_id]:<25} {cnt}")

        print(f"\nTraining set size: "
              f"{len(self.y_train)} -> "
              f"{len(self.y_train_smote)}")

        self._plot_smote_distribution(counts, counts2)

    # ─────────────────────────────────────────────────────────────
    def _plot_smote_distribution(self, before, after):
        """Plot class distribution before and after SMOTE."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        axes[0].bar(
            self.class_names, before,
            color='salmon', edgecolor='black'
        )
        axes[0].set_title('Before SMOTE')
        axes[0].set_ylabel('Count')
        axes[0].tick_params(axis='x', rotation=30)
        for i, v in enumerate(before):
            axes[0].text(i, v + 0.5, str(v), ha='center')

        axes[1].bar(
            self.class_names, after,
            color='lightgreen', edgecolor='black'
        )
        axes[1].set_title('After SMOTE (Balanced)')
        axes[1].set_ylabel('Count')
        axes[1].tick_params(axis='x', rotation=30)
        for i, v in enumerate(after):
            axes[1].text(i, v + 0.5, str(v), ha='center')

        plt.suptitle(
            'SMOTE Oversampling — Class Balance Fix',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'smote_distribution.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: smote_distribution.png")

    # ─────────────────────────────────────────────────────────────
    def _define_models(self) -> dict:
        """
        Define all classification models with
        overfitting prevention parameters.

        Returns:
            Dictionary of model name to model object
        """
        return {
            'Random Forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_leaf=5,
                max_features='sqrt',
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=150,
                max_depth=4,
                learning_rate=0.08,
                subsample=0.8,
                random_state=42
            ),
            'Decision Tree': DecisionTreeClassifier(
                max_depth=8,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=42
            ),
            'SVM': SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                class_weight='balanced',
                probability=True,
                random_state=42
            )
        }

    # ─────────────────────────────────────────────────────────────
    def train_all_models(self):
        """
        Train all four models on SMOTE-balanced data.
        Saves each model as a .pkl file.
        """
        print("\nTraining all models on SMOTE data...")
        models_def = self._define_models()

        for name, model in models_def.items():
            print(f"\n  Training {name}...")
            model.fit(
                self.X_train_smote,
                self.y_train_smote
            )
            self.models[name] = model

            # Save model
            safe_name = name.replace(' ', '_').lower()
            path = os.path.join(
                self.output_dir.replace(
                    'ModelTraining', 'Models'
                ),
                f'{safe_name}.pkl'
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            joblib.dump(model, path)
            print(f"  Saved: {safe_name}.pkl")

    # ─────────────────────────────────────────────────────────────
    def evaluate_model(self, name: str, model):
        """
        Evaluate a single model on both train and test sets.
        Stores full metrics in self.results.

        Args:
            name  : Model name string
            model : Trained sklearn model
        """
        # Predictions
        y_pred_train = model.predict(self.X_train_smote)
        y_pred_test  = model.predict(self.X_test)

        # Metrics
        train_acc = accuracy_score(
            self.y_train_smote, y_pred_train
        )
        test_acc  = accuracy_score(self.y_test, y_pred_test)

        precision = precision_score(
            self.y_test, y_pred_test,
            average='weighted', zero_division=0
        )
        recall = recall_score(
            self.y_test, y_pred_test,
            average='weighted', zero_division=0
        )
        f1 = f1_score(
            self.y_test, y_pred_test,
            average='weighted', zero_division=0
        )
        gap = train_acc - test_acc

        report = classification_report(
            self.y_test, y_pred_test,
            target_names=self.class_names,
            zero_division=0
        )
        cm = confusion_matrix(self.y_test, y_pred_test)

        # Overfitting verdict
        if gap < 0.05:
            overfit_status = 'No Overfitting'
        elif gap < 0.10:
            status_str = 'Slight Overfitting'
            overfit_status = status_str
        else:
            overfit_status = 'Overfitting'

        self.results[name] = {
            'train_accuracy' : round(train_acc, 4),
            'test_accuracy'  : round(test_acc,  4),
            'precision'      : round(precision,  4),
            'recall'         : round(recall,     4),
            'f1_score'       : round(f1,          4),
            'gap'            : round(gap,          4),
            'overfit_status' : overfit_status,
            'report'         : report,
            'confusion_matrix': cm,
            'y_pred'         : y_pred_test
        }

        print(f"\n  {name}:")
        print(f"    Train Accuracy : {train_acc:.4f}")
        print(f"    Test Accuracy  : {test_acc:.4f}")
        print(f"    Precision      : {precision:.4f}")
        print(f"    Recall         : {recall:.4f}")
        print(f"    F1 Score       : {f1:.4f}")
        print(f"    Gap            : {gap:.4f}")
        print(f"    Status         : {overfit_status}")

    # ─────────────────────────────────────────────────────────────
    def evaluate_all_models(self):
        """Evaluate all trained models."""
        print("\nEvaluating all models...")
        for name, model in self.models.items():
            self.evaluate_model(name, model)

    # ─────────────────────────────────────────────────────────────
    def plot_confusion_matrices(self):
        """Plot confusion matrix for each model."""
        for name, result in self.results.items():
            cm        = result['confusion_matrix']
            safe_name = name.replace(' ', '_').lower()

            plt.figure(figsize=(8, 6))
            sns.heatmap(
                cm, annot=True, fmt='d',
                cmap='Blues',
                xticklabels=self.class_names,
                yticklabels=self.class_names
            )
            plt.title(f'Confusion Matrix — {name}')
            plt.ylabel('Actual')
            plt.xlabel('Predicted')
            plt.xticks(rotation=30, ha='right', fontsize=8)
            plt.yticks(fontsize=8)
            plt.tight_layout()
            plt.savefig(
                os.path.join(
                    self.output_dir,
                    f'confusion_matrix_{safe_name}.png'
                ),
                dpi=100
            )
            plt.show()
            plt.close()
            print(f"Saved: confusion_matrix_{safe_name}.png")

    # ─────────────────────────────────────────────────────────────
    def plot_metrics_comparison(self):
        """
        Plot bar chart comparing all models across
        all metrics side by side.
        """
        model_names = list(self.results.keys())
        metrics     = [
            'train_accuracy', 'test_accuracy',
            'precision', 'recall', 'f1_score'
        ]
        labels = [
            'Train Acc', 'Test Acc',
            'Precision', 'Recall', 'F1'
        ]

        x     = np.arange(len(model_names))
        width = 0.15

        fig, ax = plt.subplots(figsize=(14, 6))

        colors = [
            'steelblue', 'coral',
            'green', 'purple', 'orange'
        ]

        for i, (metric, label) in enumerate(
            zip(metrics, labels)
        ):
            values = [
                self.results[m][metric]
                for m in model_names
            ]
            bars = ax.bar(
                x + i * width, values,
                width, label=label,
                color=colors[i], edgecolor='black',
                alpha=0.85
            )
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.005,
                    f'{val:.2f}',
                    ha='center', fontsize=7
                )

        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(model_names, fontsize=10)
        ax.set_ylim(0, 1.15)
        ax.set_ylabel('Score')
        ax.set_title(
            'Model Performance Comparison — All Metrics',
            fontsize=13
        )
        ax.legend(fontsize=9)
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'metrics_comparison.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: metrics_comparison.png")

    # ─────────────────────────────────────────────────────────────
    def plot_overfitting_check(self):
        """
        Plot train vs test accuracy for each model
        to visualize overfitting clearly.
        """
        model_names = list(self.results.keys())
        train_accs  = [
            self.results[m]['train_accuracy']
            for m in model_names
        ]
        test_accs   = [
            self.results[m]['test_accuracy']
            for m in model_names
        ]
        gaps        = [
            self.results[m]['gap']
            for m in model_names
        ]

        x     = np.arange(len(model_names))
        width = 0.35

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Left: Train vs Test accuracy
        axes[0].bar(
            x - width/2, train_accs, width,
            label='Train', color='steelblue',
            edgecolor='black'
        )
        axes[0].bar(
            x + width/2, test_accs, width,
            label='Test', color='coral',
            edgecolor='black'
        )
        for i, (tr, te) in enumerate(
            zip(train_accs, test_accs)
        ):
            axes[0].text(
                i - width/2, tr + 0.005,
                f'{tr:.2f}', ha='center', fontsize=8
            )
            axes[0].text(
                i + width/2, te + 0.005,
                f'{te:.2f}', ha='center', fontsize=8
            )
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(model_names, rotation=15)
        axes[0].set_ylim(0, 1.15)
        axes[0].set_title('Train vs Test Accuracy')
        axes[0].set_ylabel('Accuracy')
        axes[0].legend()

        # Right: Gap (overfitting indicator)
        bar_colors = [
            'green' if g < 0.05 else
            'orange' if g < 0.10 else
            'red'
            for g in gaps
        ]
        axes[1].bar(
            model_names, gaps,
            color=bar_colors, edgecolor='black'
        )
        axes[1].axhline(
            y=0.05, color='orange', linestyle='--',
            linewidth=1.5,
            label='Slight overfit threshold (0.05)'
        )
        axes[1].axhline(
            y=0.10, color='red', linestyle='--',
            linewidth=1.5,
            label='Overfit threshold (0.10)'
        )
        for i, g in enumerate(gaps):
            axes[1].text(
                i, g + 0.002, f'{g:.3f}',
                ha='center', fontsize=9
            )
        axes[1].set_title(
            'Overfitting Gap (Train - Test Accuracy)'
        )
        axes[1].set_ylabel('Gap')
        axes[1].tick_params(axis='x', rotation=15)
        axes[1].legend(fontsize=8)

        plt.suptitle(
            'Overfitting Analysis',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                self.output_dir,
                'overfitting_check.png'
            ),
            dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: overfitting_check.png")

    # ─────────────────────────────────────────────────────────────
    def print_final_summary(self):
        """Print complete results table for all models."""
        print("\n" + "="*75)
        print("          STEP 7 — MODEL TRAINING RESULTS SUMMARY")
        print("="*75)
        print(
            f"{'Model':<22} {'Train':>7} {'Test':>7} "
            f"{'Prec':>7} {'Rec':>7} {'F1':>7} "
            f"{'Gap':>7} {'Status'}"
        )
        print("-"*75)

        for name, res in self.results.items():
            print(
                f"{name:<22} "
                f"{res['train_accuracy']:>7.4f} "
                f"{res['test_accuracy']:>7.4f} "
                f"{res['precision']:>7.4f} "
                f"{res['recall']:>7.4f} "
                f"{res['f1_score']:>7.4f} "
                f"{res['gap']:>7.4f} "
                f"{res['overfit_status']}"
            )

        print("="*75)

        # Best model by F1
        best = max(
            self.results,
            key=lambda x: self.results[x]['f1_score']
        )
        print(f"\nBest Model (by F1): {best}")
        print(
            f"  F1 Score  : "
            f"{self.results[best]['f1_score']:.4f}"
        )
        print(
            f"  Accuracy  : "
            f"{self.results[best]['test_accuracy']:.4f}"
        )
        print(
            f"\nDetailed Classification Report ({best}):"
        )
        print(self.results[best]['report'])

    # ─────────────────────────────────────────────────────────────
    def save_results_csv(self):
        """Save all model metrics to CSV."""
        rows = []
        for name, res in self.results.items():
            rows.append({
                'Model'          : name,
                'Train_Accuracy' : res['train_accuracy'],
                'Test_Accuracy'  : res['test_accuracy'],
                'Precision'      : res['precision'],
                'Recall'         : res['recall'],
                'F1_Score'       : res['f1_score'],
                'Gap'            : res['gap'],
                'Status'         : res['overfit_status']
            })

        df_results = pd.DataFrame(rows)
        save_path  = os.path.join(
            self.output_dir, 'model_results.csv'
        )
        df_results.to_csv(save_path, index=False)
        print(f"Saved: model_results.csv")

        return df_results

    # ─────────────────────────────────────────────────────────────
    def run_training(self):
        """
        Run complete model training pipeline.

        Steps:
            1. Apply SMOTE to fix class imbalance
            2. Train all 4 models
            3. Evaluate all models
            4. Plot confusion matrices
            5. Plot metrics comparison
            6. Plot overfitting check
            7. Print final summary
            8. Save results CSV

        Returns:
            Dictionary of all model results
        """
        print("\n" + "="*55)
        print("     STEP 7: MODEL TRAINING")
        print("="*55)

        self.apply_smote()
        self.train_all_models()
        self.evaluate_all_models()
        self.plot_confusion_matrices()
        self.plot_metrics_comparison()
        self.plot_overfitting_check()
        self.print_final_summary()
        results_df = self.save_results_csv()

        print("\nStep 7 — Model Training COMPLETE!")

        return self.results, results_df

    # ─────────────────────────────────────────────────────────────
    def get_results(self) -> dict:
        """Return all model results dictionary."""
        return self.results

    def get_models(self) -> dict:
        """Return all trained model objects."""
        return self.models