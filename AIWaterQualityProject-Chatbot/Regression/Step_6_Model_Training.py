import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
import joblib
import os


class ModelTrainer:
    def __init__(self, X_train, y_train, output_dir="./Models"):
        # Impute any remaining NaNs so every model gets a fully finite matrix
        imputer = SimpleImputer(strategy="median")
        X_train_arr = imputer.fit_transform(X_train)
        self.X_train = pd.DataFrame(X_train_arr, columns=X_train.columns, index=X_train.index)
        self._imputer = imputer
        self.y_train  = y_train
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        nan_count = self.X_train.isna().sum().sum()
        if nan_count:
            print(f"[Warning] {nan_count} NaN(s) remain in X_train after imputation.")
        else:
            print(f"X_train is fully finite "
                  f"({self.X_train.shape[0]} rows, {self.X_train.shape[1]} features).")

        # Model slots
        self.rf_model = None
        self.gbr_model = None
        self.etr_model = None
        self.xgb_model = None
        self.lgbm_model = None
        self.catboost_model = None
        self.hgb_model = None
        self.stack_model = None

    def transform_test(self, X_test):
        arr = self._imputer.transform(X_test)
        return pd.DataFrame(arr, columns=X_test.columns, index=X_test.index)

    def _save(self, model, filename):
        path = os.path.join(self.output_dir, filename)
        joblib.dump(model, path)
        print(f"  Saved: {path}")
        return model

    # Random Forest
    def train_random_forest(self, rf_params=None, model_file_name="rf_wqi_predictor.pkl"):
        if rf_params is None:
            rf_params = {"n_estimators": 300, "max_depth": 10, "random_state": 42, "n_jobs": -1}
        self.rf_model = RandomForestRegressor(**rf_params)
        self.rf_model.fit(self.X_train, self.y_train)
        print("Random Forest trained.")
        return self._save(self.rf_model, model_file_name)

    # Gradient Boosting
    def train_gradient_boosting(self, gbr_params=None, model_file_name="gbr_wqi_predictor.pkl"):
        if gbr_params is None:
            gbr_params = {"n_estimators": 250, "max_depth": 6, "learning_rate": 0.05, "random_state": 42}
        self.gbr_model = GradientBoostingRegressor(**gbr_params)
        self.gbr_model.fit(self.X_train, self.y_train)
        print("Gradient Boosting trained.")
        return self._save(self.gbr_model, model_file_name)

    # Extra Trees
    def train_extra_tree(self, etr_params=None, model_file_name="etr_wqi_predictor.pkl"):
        if etr_params is None:
            etr_params = {"n_estimators": 300, "max_depth": None, "random_state": 42, "n_jobs": -1}
        self.etr_model = ExtraTreesRegressor(**etr_params)
        self.etr_model.fit(self.X_train, self.y_train)
        print("Extra Trees trained.")
        return self._save(self.etr_model, model_file_name)

    # XGBoost
    def train_XGBoost(self, xgb_params=None, model_file_name="xgb_wqi_predictor.pkl"):
        if xgb_params is None:
            xgb_params = {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8, "random_state": 42, "n_jobs": -1}
        self.xgb_model = XGBRegressor(**xgb_params)
        self.xgb_model.fit(self.X_train, self.y_train)
        print("XGBoost trained.")
        return self._save(self.xgb_model, model_file_name)

    # LightGBM
    def train_lightgbm(self, lgbm_params=None, model_file_name="lgbm_wqi_predictor.pkl"):
        if lgbm_params is None:
            lgbm_params = {"n_estimators": 500, "max_depth": -1, "learning_rate": 0.03, "num_leaves": 63, "subsample": 0.8, "colsample_bytree": 0.8, "reg_alpha": 0.1, "reg_lambda": 0.1, "random_state": 42, "n_jobs": -1, "verbose": -1}
        self.lgbm_model = LGBMRegressor(**lgbm_params)
        self.lgbm_model.fit(self.X_train, self.y_train)
        print("LightGBM trained.")
        return self._save(self.lgbm_model, model_file_name)

    # CatBoost
    def train_catboost(self, cat_params=None, model_file_name="catboost_wqi_predictor.pkl"):
        if cat_params is None:
            cat_params = {"iterations": 500, "depth": 8, "learning_rate": 0.03, "l2_leaf_reg": 3, "random_seed": 42, "verbose": 0}
        self.catboost_model = CatBoostRegressor(**cat_params)
        self.catboost_model.fit(self.X_train, self.y_train)
        print("CatBoost trained.")
        return self._save(self.catboost_model, model_file_name)

    # HistGradientBoosting
    def train_hist_gbm(self, hgb_params=None, model_file_name="hgb_wqi_predictor.pkl"):
        if hgb_params is None:
            hgb_params = {"max_iter": 500, "max_depth": 8, "learning_rate": 0.03, "l2_regularization": 0.1, "random_state": 42}
        self.hgb_model = HistGradientBoostingRegressor(**hgb_params)
        self.hgb_model.fit(self.X_train, self.y_train)
        print("HistGradientBoosting trained.")
        return self._save(self.hgb_model, model_file_name)

    # Stacking Ensemble
    # Base learners: XGBoost + LightGBM + CatBoost + RF
    # Meta-learner : Ridge regression
    def train_stacking(self, model_file_name="stack_wqi_predictor.pkl"):
        estimators = [
            ("xgb", XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)),
            ("lgbm", LGBMRegressor(n_estimators=500, learning_rate=0.03, num_leaves=63, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1, verbose=-1)),
            ("catboost", CatBoostRegressor(iterations=500, depth=8, learning_rate=0.03, random_seed=42, verbose=0)),
            ("rf",       RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1)),
        ]
        self.stack_model = StackingRegressor(
            estimators=estimators,
            final_estimator=Ridge(alpha=1.0),
            cv=5,
            n_jobs=-1
        )
        self.stack_model.fit(self.X_train, self.y_train)
        print("Stacking Ensemble trained.")
        return self._save(self.stack_model, model_file_name)

    # ── Dispatcher ────────────────────────────────────────────────────────────
    def train_model(self, model_name, params=None, model_file_name=None):
        name = model_name.lower()
        dispatch = {
            "rf": (self.train_random_forest, "rf_wqi_predictor.pkl", {"rf_params":    params}),
            "gbr": (self.train_gradient_boosting,"gbr_wqi_predictor.pkl", {"gbr_params":   params}),
            "etr": (self.train_extra_tree, "etr_wqi_predictor.pkl", {"etr_params":   params}),
            "xgb": (self.train_XGBoost, "xgb_wqi_predictor.pkl", {"xgb_params":   params}),
            "lgbm": (self.train_lightgbm, "lgbm_wqi_predictor.pkl", {"lgbm_params":  params}),
            "catboost": (self.train_catboost, "catboost_wqi_predictor.pkl", {"cat_params":   params}),
            "hgb": (self.train_hist_gbm, "hgb_wqi_predictor.pkl", {"hgb_params":   params}),
            "stack": (self.train_stacking, "stack_wqi_predictor.pkl", {}),
        }
        if name not in dispatch:
            raise ValueError(
                f"Unknown model '{model_name}'. "
                "Choose from: rf, gbr, etr, xgb, lgbm, catboost, hgb, stack."
            )
        fn, default_fname, kwargs = dispatch[name]
        kwargs["model_file_name"] = model_file_name or default_fname
        if name == "stack":
            return fn(model_file_name=kwargs["model_file_name"])
        return fn(**kwargs)