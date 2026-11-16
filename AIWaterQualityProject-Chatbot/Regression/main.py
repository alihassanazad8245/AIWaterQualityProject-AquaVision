import warnings
warnings.filterwarnings(
    "ignore",
    message="R.2 score is not well-defined",
    category=UserWarning
)
warnings.filterwarnings(

    "ignore",
    message="R^2 score is not well-defined",
    category=UserWarning
)
from sklearn.exceptions import UndefinedMetricWarning
warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
warnings.filterwarnings("ignore", message="One or more of the test scores are non-finite")

from Step_1_Data_Preparation import DataPreparation
from Step_2_EDA import EDA
from Step_3_Data_Transformation import DataTransform
from Step_4_FeatureSelection import FeatureSelection
from Step_5_Train_Test_DataSplit import DataSplitter
from Step_6_Model_Training import ModelTrainer
from Step_7_ModelTesting_PerformanceEvaluation import ModelEvaluator
from Step_8_Cross_Validation import LogoCrossValidation
from Step_9_HyperParameterOptimization import LogoGridSearch
from Step_10_Model_Comparison import ModelComparator

from sklearn.impute import SimpleImputer
from catboost import CatBoostRegressor
import pandas as pd

# Output directories
output_dirs = {
    'Datapreparation':  "./Datapreparation",
    'EDA':              "./EDA",
    'MissingValuegraph':"./MissingValuegraph",
    'FeatureSelection': "./FeatureSelection",
    'ModelTraining':    "./ModelTraining",
    'Models':           "./Models",
    'ModelComparison':  "./ModelComparison"
}

# STEP 1 — Data Preparation
print("\nSTEP 1 — Data Preparation")

preparation = DataPreparation(data_path="merge.csv",output_dirs=output_dirs)
preparation.run_pipeline()

# STEP 2 — Exploratory Data Analysis
print("\nSTEP 2 — Exploratory Data Analysis")

eda = EDA(df=preparation.df, df_model_ready=preparation.df_model_ready, output_dir=output_dirs['EDA'])
city_rmse, baseline_city, baseline_rmse = eda.run_eda()

print(f"\nBaseline city : {baseline_city}")
print(f"Baseline RMSE : {baseline_rmse:.4f}")


# STEP 3 — Data Transformation
print("\nSTEP 3 — Data Transformation")

transformer    = DataTransform(df=preparation.df_model_ready)
df_transformed = transformer.run_transformation()

# STEP 4 — Feature Selection
print("STEP 4 — Feature Selection")

feature_selector = FeatureSelection(df_transformed)
df_selected, selected_features = feature_selector.run_feature_selection(idx_s=0, idx_e=len(df_transformed.columns) - 1, threshold=0.05)

# STEP 5 — Train / Test Split  (80 / 20 random split)
print("\nSTEP 5 — Train Test Split")

splitter = DataSplitter(df_selected=df_selected, df=preparation.df_model_ready, selected_features=selected_features)
X_train, X_test, y_train, y_test, _, _ = splitter.run_split()

imp    = SimpleImputer(strategy="median")
X_train = pd.DataFrame(imp.fit_transform(X_train), columns=X_train.columns, index=X_train.index)
X_test  = pd.DataFrame(imp.transform(X_test), columns=X_test.columns, index=X_test.index)
X_full  = pd.DataFrame(imp.transform(splitter.X), columns=splitter.X.columns, index=splitter.X.index)
y_full  = splitter.y

nan_left = X_train.isna().sum().sum()
print(f"NaN check — X_train after imputation: " f"{nan_left} ({'clean' if nan_left == 0 else 'WARNING'})")

# STEP 6 — Model Training  (8 models)
print("\nSTEP 6 — Model Training")

trainer = ModelTrainer(X_train=X_train, y_train=y_train, output_dir=output_dirs['Models'])

print("\n--- Random Forest ---")
rf_model = trainer.train_model("rf", params={"n_estimators": 300, "max_depth": 10, "random_state": 42}, model_file_name="rf_initial.pkl")

print("\n--- Gradient Boosting ---")
gbr_model = trainer.train_model("gbr", params={"n_estimators": 250, "max_depth": 6, "learning_rate": 0.05, "random_state": 42}, model_file_name="gbr_initial.pkl")

print("\n--- Extra Trees ---")
etr_model = trainer.train_model("etr", params={"n_estimators": 300, "max_depth": None, "random_state": 42, "n_jobs": -1}, model_file_name="etr_initial.pkl")

print("\n--- XGBoost ---")
xgb_model = trainer.train_model("xgb", params={"n_estimators": 300, "max_depth": 6, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8, "random_state": 42, "n_jobs": -1}, model_file_name="xgb_initial.pkl")

print("\n--- LightGBM ---")
lgbm_model = trainer.train_model("lgbm", params={"n_estimators": 500, "max_depth": -1, "learning_rate": 0.03, "num_leaves": 63, "subsample": 0.8, "colsample_bytree": 0.8, "reg_alpha": 0.1, "reg_lambda": 0.1, "random_state": 42, "n_jobs": -1, "verbose": -1}, model_file_name="lgbm_initial.pkl")

print("\n--- CatBoost ---")
catboost_model = trainer.train_model("catboost", params={"iterations": 500, "depth": 8, "learning_rate": 0.03, "l2_leaf_reg": 3, "random_seed": 42, "verbose": 0}, model_file_name="catboost_initial.pkl")

print("\n--- HistGradientBoosting ---")
hgb_model = trainer.train_model("hgb", params={"max_iter": 500, "max_depth": 8, "learning_rate": 0.03, "l2_regularization": 0.1, "random_state": 42}, model_file_name="hgb_initial.pkl")

print("\n--- Stacking Ensemble (XGB + LGBM + CatBoost + RF → Ridge) ---")
stack_model = trainer.train_model("stack", model_file_name="stack_initial.pkl")

# STEP 7 — Model Evaluation
print("\nSTEP 7 — Model Evaluation")

all_models = [
    (rf_model, "Random Forest"),
    (gbr_model, "Gradient Boosting"),
    (etr_model, "Extra Trees"),
    (xgb_model, "XGBoost"),
    (lgbm_model, "LightGBM"),
    (catboost_model, "CatBoost"),
    (hgb_model, "HistGBM"),
    (stack_model, "Stacking"),
]

eval_results = {}
for model_obj, model_label in all_models:
    evaluator = ModelEvaluator(X_test, y_test, model_obj, model_label, output_dir=output_dirs['ModelTraining'])
    metrics = evaluator.run_full_evaluation()
    eval_results[model_label] = metrics

# STEP 8 — 5-Fold Cross-Validation
print("\nSTEP 8 — 5-Fold Cross-Validation")

cv_models = [
    (xgb_model, "XGBoost"),
    (lgbm_model, "LightGBM"),
    (catboost_model, "CatBoost"),
    (stack_model, "Stacking"),
]

for model_obj, model_label in cv_models:
    print(f"\nCV: {model_label}")
    cv = LogoCrossValidation(
        X=X_full, y=y_full,
        model=model_obj,
        model_name=model_label
    )
    cv.run_logo_cv()
    cv.summary()

# STEP 9 — Hyperparameter Optimisation (CatBoostRegressor tuned on R²)
print("\nSTEP 9 — Hyperparameter Optimisation (CatBoost, scored by R²)")

cat_param_grid = {
    "iterations": [300, 500, 700],
    "depth": [4, 6, 8, 10],
    "learning_rate": [0.01, 0.03, 0.05],
    "l2_leaf_reg": [1, 3, 5],
}

cat_gs = LogoGridSearch(
    model=CatBoostRegressor(random_seed=42, verbose=0),
    param_grid=cat_param_grid,
    X=X_full,
    y=y_full,
    scoring_type="r2",
    n_splits=5,
    model_name="CatBoost"
)
cat_grid_result = cat_gs.run()

# Retrain best CatBoost on training set only
cat_best = cat_grid_result.best_estimator_
cat_best.fit(X_train, y_train)

print(f"Best CatBoost R² : {cat_gs.best_score_:.4f}")
print(f"Best CatBoost Params: {cat_gs.best_params_}")

# STEP 10 — Final Evaluation & Model Comparison
print("\nSTEP 10 — Final Model Comparison")

# Evaluate tuned CatBoost
cat_best_eval = ModelEvaluator(
    X_test, y_test,
    cat_best, "CatBoost Tuned",
    output_dir=output_dirs['ModelTraining']
)
cat_best_metrics = cat_best_eval.run_full_evaluation()
eval_results["CatBoost Tuned"] = cat_best_metrics

comparator = ModelComparator(output_dir=output_dirs['ModelComparison'])

comparison_df = comparator.compare_multiple_models(
    models=[(name, m) for name, m in eval_results.items()]
)

# Sort by R² descending for easy reading
comparison_df = comparison_df.sort_values("R2_Score", ascending=False).reset_index(drop=True)

print("\nFINAL MODEL COMPARISON  (sorted by R²)")
print(comparison_df.to_string(index=False))

comparison_df.to_csv(
    f"{output_dirs['ModelComparison']}/final_model_comparison.csv", index=False
)

# Print the winner
best_row = comparison_df.iloc[0]
print(f"\nBest model : {best_row['Model']}")
print(f"R2 Score : {best_row['R2_Score']:.4f}")
print(f"RMSE : {best_row['RMSE']:.4f}")
print(f"MAE : {best_row['MAE']:.4f}")

print("PIPELINE COMPLETED SUCCESSFULLY")