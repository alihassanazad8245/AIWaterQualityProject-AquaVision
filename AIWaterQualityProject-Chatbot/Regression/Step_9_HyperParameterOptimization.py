import warnings
import numpy as np
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.metrics import make_scorer, mean_squared_error
from sklearn.exceptions import UndefinedMetricWarning


class LogoGridSearch:
    def __init__(self, model, param_grid, X, y, scoring_type="r2", verbose=1, n_splits=5, model_name=None):

        self.model = model
        self.param_grid = param_grid
        self.X = X
        self.y = y
        self.scoring_type = scoring_type
        self.verbose = verbose
        self.n_splits = n_splits
        self.model_name = model_name if model_name else type(model).__name__

        self.best_params_ = None
        self.best_score_ = None

    # RMSE scorer
    @staticmethod
    def rmse_score(y_true, y_pred):
        return np.sqrt(mean_squared_error(y_true, y_pred))

    # Scorer wrapper
    def _get_scorer(self):
        if self.scoring_type == "rmse":
            return make_scorer(self.rmse_score, greater_is_better=False)
        elif self.scoring_type == "r2":
            return "r2"
        else:
            raise ValueError("scoring_type must be 'rmse' or 'r2'")

    # Run grid search
    def run(self):
        print(f"\n[INFO] GridSearch: {self.model_name} | "
              f"metric: {self.scoring_type.upper()} | "
              f"folds: {self.n_splits}")

        cv = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)
        y  = np.ravel(self.y)

        grid = GridSearchCV(
            estimator  = self.model,
            param_grid = self.param_grid,
            scoring    = self._get_scorer(),
            cv         = cv,
            n_jobs     = -1,
            verbose    = self.verbose
        )

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
            grid.fit(self.X, y)

        self.best_params_ = grid.best_params_

        if self.scoring_type == "r2":
            self.best_score_ = grid.best_score_
        else:
            self.best_score_ = -grid.best_score_

        print(f"\n[RESULT] {self.model_name} GridSearch done")
        print(f"Best {self.scoring_type.upper():13s}: {self.best_score_:.4f}")
        print(f"Best Parameters : {self.best_params_}\n")

        return grid