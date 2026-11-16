# Main orchestrator for WQI time-series forecasting pipeline

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from Step_1_Data_Ingestion import DataIngestion
from Step_2_EDA import TimeSeriesEDA
from Step_3_Data_Preparation import DataPreparation
from Step_4_Train_Test_Split import TrainTestSplitter
from Step_5_Model_Training import TimeSeriesModelTrainer
from Step_6_Evaluation import TimeSeriesEvaluator
from Step_7_Cross_Validation import WalkForwardCV
from Step_8_HyperParameterOptimization import TimeSeriesHPO
from Step_9_Forecasting import Forecaster
from Step_10_Model_Comparison import ModelComparator

OUTPUT_DIRS = {
    "DataIngestion": "./DataIngestion",
    "MissingValues": "./MissingValues",
    "EDA": "./EDA",
    "DataPrep": "./DataPreparation",
    "DataSplit": "./DataSplit",
    "Models": "./Models",
    "Evaluation": "./Evaluation",
    "Forecasts": "./Forecasts",
    "Comparison": "./ModelComparison",
}

# Output of Step_1_DataPreparation.py + Step_2_WQICalculation.py
# (run those two scripts first — they write merge.csv into ./WQIResults/
# with a properly computed "Risk_Score" column, ready for forecasting)
DATA_PATH = "merge.csv"
TARGET_COL = "Risk_Score"
FREQ = "ME"
TEST_SIZE = 0.20
LOOK_BACK = 12
N_FORECAST = 12

ARIMA_ORDER = (1, 1, 1)
SARIMA_ORDER = (1, 1, 1)
SARIMA_SEASONAL = (1, 1, 1, 12)

RUN_HPO = False
RUN_CV = True
N_SPLITS = 5

print("\n" + "=" * 60)
print(" STEP 1 — DATA INGESTION")
print("=" * 60)

ingestion = DataIngestion(
    data_path=DATA_PATH,
    target_col=TARGET_COL,
    freq=FREQ,
    output_dirs={
        "DataIngestion": OUTPUT_DIRS["DataIngestion"],
        "MissingValues": OUTPUT_DIRS["MissingValues"],
    },
)
ts_df = ingestion.run_pipeline()

print(f"\nResampled time-series shape: {ts_df.shape}")
print(ts_df[TARGET_COL].describe())

print("\n" + "=" * 60)
print(" STEP 2 — EXPLORATORY DATA ANALYSIS")
print("=" * 60)

eda = TimeSeriesEDA(
    ts_df=ts_df,
    target_col=TARGET_COL,
    output_dir=OUTPUT_DIRS["EDA"],
)
stationarity = eda.run_eda()

adf_stationary = stationarity["ADF"]["Stationary"]
d_suggested = 0 if adf_stationary else 1
print(f"\nADF stationary={adf_stationary}  →  suggested d = {d_suggested}")

ARIMA_ORDER = (ARIMA_ORDER[0], d_suggested, ARIMA_ORDER[2])
SARIMA_ORDER = (SARIMA_ORDER[0], d_suggested, SARIMA_ORDER[2])

print("\n" + "=" * 60)
print(" STEP 3 — DATA PREPARATION")
print("=" * 60)

prep_step = DataPreparation(
    ts_df=ts_df,
    target_col=TARGET_COL,
    look_back=LOOK_BACK,
    output_dir=OUTPUT_DIRS["DataPrep"],
)
prep_data = prep_step.run_preparation(test_size=TEST_SIZE)

series = prep_data["series"]
scaler = prep_data["scaler"]

print("\n" + "=" * 60)
print(" STEP 4 — TRAIN / TEST SPLIT")
print("=" * 60)

splitter = TrainTestSplitter(
    series=series,
    test_size=TEST_SIZE,
    n_splits=N_SPLITS,
    output_dir=OUTPUT_DIRS["DataSplit"],
)
train_series, test_series = splitter.run_split()

print("\n" + "=" * 60)
print(" STEP 5 — MODEL TRAINING")
print("=" * 60)

trainer = TimeSeriesModelTrainer(
    train_series=train_series,
    prep_data=prep_data,
    output_dir=OUTPUT_DIRS["Models"],
)

print("\n--- ARIMA ---")
arima_model = trainer.train_model(
    "arima",
    params={"order": ARIMA_ORDER},
    model_file_name="arima_model.pkl",
)

print("\n--- SARIMA ---")
sarima_model = trainer.train_model(
    "sarima",
    params={
        "order": SARIMA_ORDER,
        "seasonal_order": SARIMA_SEASONAL,
    },
    model_file_name="sarima_model.pkl",
)

print("\n--- Prophet ---")
prophet_model = trainer.train_model(
    "prophet",
    params={
        "changepoint_prior_scale": 0.05,
        "seasonality_mode": "additive",
    },
    model_file_name="prophet_model.pkl",
)

print("\n--- LSTM ---")
lstm_model = trainer.train_model(
    "lstm",
    params={
        "units_1": 64,
        "units_2": 32,
        "dropout": 0.2,
        "epochs": 100,
        "batch_size": 16,
        "patience": 15,
    },
    model_file_name="lstm_model.keras",
)

print("\n" + "=" * 60)
print(" STEP 6 — MODEL EVALUATION")
print("=" * 60)

eval_results = {}
test_index = test_series.index

def predict_stat(fitted, n):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fitted.get_forecast(steps=n).predicted_mean.values

if arima_model is not None:
    y_pred_arima = predict_stat(arima_model, len(test_series))
    ev = TimeSeriesEvaluator("ARIMA", output_dir=OUTPUT_DIRS["Evaluation"])
    eval_results["ARIMA"] = ev.run_full_evaluation(
        y_true=test_series.values,
        y_pred=y_pred_arima,
        train_series=train_series,
        index=test_index,
    )

if sarima_model is not None:
    y_pred_sarima = predict_stat(sarima_model, len(test_series))
    ev = TimeSeriesEvaluator("SARIMA", output_dir=OUTPUT_DIRS["Evaluation"])
    fc_frame = sarima_model.get_forecast(len(test_series)).summary_frame()
    eval_results["SARIMA"] = ev.run_full_evaluation(
        y_true=test_series.values,
        y_pred=y_pred_sarima,
        train_series=train_series,
        conf_lower=fc_frame["mean_ci_lower"].values,
        conf_upper=fc_frame["mean_ci_upper"].values,
        index=test_index,
    )

if prophet_model is not None:
    try:
        future = prophet_model.make_future_dataframe(
            periods=len(test_series), freq=FREQ
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc_prop = prophet_model.predict(future)
        y_pred_prop = fc_prop["yhat"].tail(len(test_series)).values
        ev = TimeSeriesEvaluator("Prophet", output_dir=OUTPUT_DIRS["Evaluation"])
        eval_results["Prophet"] = ev.run_full_evaluation(
            y_true=test_series.values,
            y_pred=y_pred_prop,
            train_series=train_series,
            conf_lower=fc_prop["yhat_lower"].tail(len(test_series)).values,
            conf_upper=fc_prop["yhat_upper"].tail(len(test_series)).values,
            index=test_index,
        )
    except Exception as exc:
        print(f"[WARN] Prophet evaluation failed: {exc}")

if lstm_model is not None:
    X_test_seq = prep_data["X_test_seq"]
    y_test_seq = prep_data["y_test_seq"]

    y_pred_sc = lstm_model.predict(X_test_seq, verbose=0).flatten()
    y_pred_lstm = scaler.inverse_transform(y_pred_sc.reshape(-1, 1)).flatten()
    y_true_lstm = scaler.inverse_transform(y_test_seq.reshape(-1, 1)).flatten()

    lstm_test_index = series.index[-len(y_true_lstm):]

    ev = TimeSeriesEvaluator("LSTM", output_dir=OUTPUT_DIRS["Evaluation"])
    eval_results["LSTM"] = ev.run_full_evaluation(
        y_true=y_true_lstm,
        y_pred=y_pred_lstm,
        train_series=train_series,
        index=lstm_test_index,
    )

if RUN_CV:
    print("\n" + "=" * 60)
    print(" STEP 7 — WALK-FORWARD CROSS-VALIDATION")
    print("=" * 60)

    cv = WalkForwardCV(series=series, n_splits=N_SPLITS)

    if arima_model is not None:
        df_cv = cv.cv_arima(order=ARIMA_ORDER)
        cv.summary(model_name="ARIMA")

    if sarima_model is not None:
        df_cv = cv.cv_sarima(
            order=SARIMA_ORDER, seasonal_order=SARIMA_SEASONAL
        )
        cv.summary(model_name="SARIMA")

    if lstm_model is not None:
        df_cv = cv.cv_lstm(
            scaler=scaler,
            look_back=LOOK_BACK,
            units_1=64,
            units_2=32,
            dropout=0.2,
            epochs=30,
            batch_size=16,
        )
        cv.summary(model_name="LSTM")

if RUN_HPO:
    print("\n" + "=" * 60)
    print(" STEP 8 — HYPERPARAMETER OPTIMISATION")
    print("=" * 60)

    hpo = TimeSeriesHPO(series=train_series, n_splits=N_SPLITS)

    arima_hpo = hpo.arima_order_search()
    best_arima_order = arima_hpo["best_order"]

    sarima_hpo = hpo.sarima_order_search()
    best_sarima_order = sarima_hpo["best_order"]
    best_sarima_so = sarima_hpo["best_seasonal_order"]

    lstm_hpo = hpo.lstm_param_search()
    best_lstm = lstm_hpo.get("best_params", {})

    trainer2 = TimeSeriesModelTrainer(
        train_series=train_series,
        prep_data=prep_data,
        output_dir=OUTPUT_DIRS["Models"],
    )

    if best_arima_order:
        arima_model = trainer2.train_model(
            "arima",
            params={"order": best_arima_order},
            model_file_name="arima_best.pkl",
        )

    if best_sarima_order:
        sarima_model = trainer2.train_model(
            "sarima",
            params={
                "order": best_sarima_order,
                "seasonal_order": best_sarima_so,
            },
            model_file_name="sarima_best.pkl",
        )

    if best_lstm:
        lstm_model = trainer2.train_model(
            "lstm",
            params=best_lstm,
            model_file_name="lstm_best.keras",
        )

print("\n" + "=" * 60)
print(f" STEP 9 — FUTURE FORECASTING  ({N_FORECAST} steps)")
print("=" * 60)

forecaster = Forecaster(
    full_series=series,
    scaler=scaler,
    look_back=LOOK_BACK,
    freq=FREQ,
    output_dir=OUTPUT_DIRS["Forecasts"],
)

all_forecasts = forecaster.run_forecast(
    n_steps=N_FORECAST,
    arima_model=arima_model,
    sarima_model=sarima_model,
    prophet_model=prophet_model,
    lstm_model=lstm_model,
)

print("\n" + "=" * 60)
print(" STEP 10 — FINAL MODEL COMPARISON")
print("=" * 60)

comparator = ModelComparator(output_dir=OUTPUT_DIRS["Comparison"])
comparison_df = comparator.compare_models(list(eval_results.values()))
comparator.print_leaderboard(comparison_df)

comparison_df.to_csv(
    f"{OUTPUT_DIRS['Comparison']}/final_comparison.csv", index=False
)

print("\n" + "=" * 60)
print(" PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 60)