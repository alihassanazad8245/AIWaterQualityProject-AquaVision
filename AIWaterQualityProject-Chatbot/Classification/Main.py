"""
Main.py``````

Entry point for Water Quality Classification Project.
Runs the complete pipeline step by step.

Dataset  : Pakistan Water Quality Dataset (706 samples)
Task     : Classify water quality using WHO guidelines
"""

from Step_1_DataPreparation    import DataPreparation
from Step_2_WQICalculation     import WQICalculation
from Step_3_EDA                import EDA
from Step_4_DataTransformation import DataTransformation
from Step_5_FeatureSelection   import FeatureSelection
from Step_6_TrainTestSplit     import TrainTestSplit
from Step_7_ModelTraining      import ModelTraining
from Step_8_DataSampling              import DataSampler
from Step_9_Cross_Validation         import CrossValidator
from Step_10_HyperparameterOptimization import HyperparameterOptimizer
from Step_11_Model_Comparison        import ModelComparator
# ── Output Directories ─────────────────────────────────────────
OUTPUT_DIRS = {
    'MissingValuegraph' : './MissingValuegraph',
    'EDA'               : './EDA',
    'WQIResults'        : './WQIResults',
    'FeatureSelection'  : './FeatureSelection',
    'ModelTraining'     : './ModelTraining',
    'ModelComparison'   : './ModelComparison',
    'Models'            : './Models',
    'TransformedData'   : './TransformedData',
}

# ══════════════════════════════════════════════════════════════
# STEP 1 — DATA PREPARATION
# ══════════════════════════════════════════════════════════════
preparation = DataPreparation(
    file_path='./data/wq_pakistan.xlsx',
    output_dirs=OUTPUT_DIRS
)
df = preparation.run_pipeline()

# ══════════════════════════════════════════════════════════════
# STEP 2 — WQI CALCULATION
# ══════════════════════════════════════════════════════════════
wqi_calc = WQICalculation(
    df=df,
    output_dir=OUTPUT_DIRS['WQIResults']
)
df = wqi_calc.run_wqi_pipeline()

# ══════════════════════════════════════════════════════════════
# STEP 3 — EDA
# ══════════════════════════════════════════════════════════════
eda = EDA(
    df=df,
    output_dir=OUTPUT_DIRS['EDA']
)
eda.run_eda()

# ══════════════════════════════════════════════════════════════
# STEP 4 — DATA TRANSFORMATION
# ══════════════════════════════════════════════════════════════
transformer = DataTransformation(
    df=df,
    output_dir=OUTPUT_DIRS['TransformedData']
)
df_transformed = transformer.run_transformation()

# ══════════════════════════════════════════════════════════════
# STEP 5 — FEATURE SELECTION
# ══════════════════════════════════════════════════════════════
feature_selector = FeatureSelection(
    df=df_transformed,
    output_dir=OUTPUT_DIRS['FeatureSelection']
)
selected_features = feature_selector.run_feature_selection(
    top_n=12
)

# ══════════════════════════════════════════════════════════════
# STEP 6 — TRAIN/TEST SPLIT
# ══════════════════════════════════════════════════════════════
splitter = TrainTestSplit(
    df=df_transformed,
    selected_features=selected_features,
    output_dir=OUTPUT_DIRS['ModelTraining']
)
X_train, X_test, y_train, y_test, \
class_names, label_encoder = splitter.run_split()

# ══════════════════════════════════════════════════════════════
# STEP 7 — MODEL TRAINING
# ══════════════════════════════════════════════════════════════
trainer = ModelTraining(
    X_train=X_train,
    X_test=X_test,
    y_train=y_train,
    y_test=y_test,
    class_names=class_names,
    output_dir=OUTPUT_DIRS['ModelTraining']
)
results, results_df = trainer.run_training()

print("\nSteps 1 to 7 Complete!")
print(results_df.to_string(index=False))

# ══════════════════════════════════════════════════════════════
# STEP 8 — DATA SAMPLING
# ══════════════════════════════════════════════════════════════
sampler = DataSampler(
    X=X_train,
    y=y_train
)

X_sample, y_sample = sampler.get_sample(n_samples=500)


# ══════════════════════════════════════════════════════════════
# STEP 9 — CROSS VALIDATION
# ══════════════════════════════════════════════════════════════

# 🔥 IMPORTANT: Extract best model from Step 7
# Your trainer returns results — we need actual model objects

trained_models = trainer.models   # <-- THIS MUST EXIST in your Step 7 class

# Select best model (you already know GB is best, but we do it programmatically)
best_model_name = results_df.sort_values(by="F1_Score", ascending=False).iloc[0]["Model"]
best_model = trained_models[best_model_name]

print(f"\nBest model selected for CV: {best_model_name}")

cv = CrossValidator(
    model=best_model,
    model_name=best_model_name,
    X=X_sample,
    y=y_sample
)

cv_results = cv.run(
    save_path=f"{OUTPUT_DIRS['ModelComparison']}/cv_results.csv"
)


# ══════════════════════════════════════════════════════════════
# STEP 10 — HYPERPARAMETER OPTIMIZATION
# ══════════════════════════════════════════════════════════════

optimizer = HyperparameterOptimizer(
    X_train=X_train,
    y_train=y_train
)

best_tuned_model, best_params, best_score = optimizer.run(
    save_path=f"{OUTPUT_DIRS['ModelComparison']}/gb_tuning_results.csv"
)

print("\nTuned Model Ready.")


# ══════════════════════════════════════════════════════════════
# STEP 11 — FINAL MODEL COMPARISON
# ══════════════════════════════════════════════════════════════

# Combine original + tuned model
models_dict = trained_models.copy()
models_dict["GB (Tuned)"] = best_tuned_model

comparator = ModelComparator(
    models_dict=models_dict,
    X_test=X_test,
    y_test=y_test
)

final_results = comparator.evaluate_all(
    save_path=f"{OUTPUT_DIRS['ModelComparison']}/final_model_results.csv"
)


print("\nAll Steps (1–11) Completed Successfully!")
print("\nFinal Model Ranking:")
print(final_results.to_string(index=False))