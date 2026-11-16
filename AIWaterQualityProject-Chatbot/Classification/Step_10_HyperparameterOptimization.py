import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier

class HyperparameterOptimizer:
    def __init__(self, X_train, y_train, random_state=42):
        self.X_train = X_train
        self.y_train = y_train
        self.random_state = random_state
        self.grid_ = None
        self.best_model_ = None

    def _print_header(self):
        print("\n" + "="*55)
        print("     STEP 10: HYPERPARAMETER OPTIMIZATION")
        print("="*55)
        print("Model: Gradient Boosting (Classifier)")

    def run(self, save_path="gb_tuning_results.csv"):
        self._print_header()

        param_grid = {
            "n_estimators": [100, 150, 200],
            "learning_rate": [0.05, 0.1],
            "max_depth": [3, 5],
            "subsample": [0.8, 1.0]
        }

        estimator = GradientBoostingClassifier(random_state=self.random_state)

        grid = GridSearchCV(
            estimator=estimator,
            param_grid=param_grid,
            scoring="f1_weighted",
            cv=5,
            n_jobs=-1,
            verbose=1
        )

        grid.fit(self.X_train, self.y_train)

        self.grid_ = grid
        self.best_model_ = grid.best_estimator_

        print("\nBest Parameters:")
        print(grid.best_params_)
        print(f"Best CV Score (F1_w): {grid.best_score_:.4f}")

        # save full results
        results = pd.DataFrame(grid.cv_results_)
        results.to_csv(save_path, index=False)
        print(f"Saved: {save_path}")

        return self.best_model_, grid.best_params_, grid.best_score_