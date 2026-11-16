import os
import warnings
import numpy as np
import pandas as pd
import joblib
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

try:
    from prophet import Prophet
    _PROPHET_OK = True
except ImportError:
    _PROPHET_OK = False
    print("prophet not installed — Prophet model will be skipped.")

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    _TF_OK = True
except ImportError:
    _TF_OK = False
    print("TensorFlow not installed — LSTM model will be skipped.")


# trains time series models
class TimeSeriesModelTrainer:

    # initializes model trainer
    def __init__(self, train_series, prep_data, output_dir = "./Models"):
        self.train = train_series
        self.prep = prep_data
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # saves model using joblib
    def _save_joblib(self, obj, filename: str):
        path = os.path.join(self.output_dir, filename)
        joblib.dump(obj, path)
        print(f"  Saved to {filename}")
        return obj

    # trains arima model
    def train_arima(self, order = (1, 1, 1), model_file_name: str = "arima_model.pkl"):
        print(f"\n  Fitting ARIMA{order} on {len(self.train)} observations …")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted = ARIMA(self.train, order=order).fit()
        print(f"  AIC = {fitted.aic:.2f}   BIC = {fitted.bic:.2f}")
        return self._save_joblib(fitted, model_file_name)

    # trains sarima model
    def train_sarima(self, order = (1, 1, 1), seasonal_order = (1, 1, 1, 12), model_file_name = "sarima_model.pkl",):
        s = seasonal_order[3]
        if len(self.train) < 2 * s:
            print(f"[SKIP] SARIMA needs ≥{2*s} training obs "
                  f"(have {len(self.train)}).")
            return None

        print(f"\n Fitting SARIMA{order}×{seasonal_order} …")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted = SARIMAX( self.train, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        print(f"  AIC = {fitted.aic:.2f}   BIC = {fitted.bic:.2f}")
        return self._save_joblib(fitted, model_file_name)

    # trains prophet model
    def train_prophet(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_mode: str = "additive",
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = False,
        daily_seasonality: bool = False,
        model_file_name: str = "prophet_model.pkl",
    ):
        if not _PROPHET_OK:
            print("  [SKIP] Prophet not installed.")
            return None

        df_prophet = pd.DataFrame({
            "ds": self.train.index,
            "y":  self.train.values,
        })
        print(f"\n  Fitting Prophet on {len(df_prophet)} observations …")
        model = Prophet(
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(df_prophet)

        print("  Prophet trained.")
        return self._save_joblib(model, model_file_name)

    # trains lstm model
    def train_lstm(
        self,
        units_1: int = 64,
        units_2: int = 32,
        dropout: float = 0.2,
        epochs: int = 100,
        batch_size: int = 16,
        patience: int = 15,
        model_file_name: str = "lstm_model.keras",
    ):
        if not _TF_OK:
            print("  [SKIP] TensorFlow not installed.")
            return None

        X_train = self.prep["X_train_seq"]
        y_train = self.prep["y_train_seq"]
        look_back = self.prep["look_back"]

        print(f"\n  Building LSTM  (units={units_1}/{units_2}, "
              f"dropout={dropout}, epochs={epochs}) …")

        model = Sequential([
            LSTM(units_1, activation="tanh", return_sequences=True,
                 input_shape=(look_back, 1)),
            Dropout(dropout),
            LSTM(units_2, activation="tanh", return_sequences=False),
            Dropout(dropout),
            Dense(1),
        ])
        model.compile(optimizer="adam", loss="mse")
        model.summary()

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=patience,
                          restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                              patience=patience // 2, verbose=1),
        ]

        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            callbacks=callbacks,
            verbose=1,
        )

        self._plot_lstm_loss(history)

        path = os.path.join(self.output_dir, model_file_name)
        model.save(path)
        print(f"  LSTM saved → {model_file_name}")
        return model

    # plots lstm training loss
    def _plot_lstm_loss(self, history):
        plt_path = os.path.join(self.output_dir, "lstm_training_loss.png")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 4))
        plt.plot(history.history["loss"],     label="Train Loss")
        plt.plot(history.history["val_loss"], label="Val Loss")
        plt.title("LSTM Training Loss Curve", fontsize=13)
        plt.xlabel("Epoch"); plt.ylabel("MSE Loss")
        plt.legend(); plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(plt_path, dpi=150)
        plt.close()
        print(f"  Loss curve saved.")

    # trains selected model
    def train_model(
        self,
        model_name: str,
        params: dict = None,
        model_file_name: str = None,
    ):
        name = model_name.lower()
        params  = params or {}
        _fnames = {
            "arima":   "arima_model.pkl",
            "sarima":  "sarima_model.pkl",
            "prophet": "prophet_model.pkl",
            "lstm":    "lstm_model.keras",
        }
        if name not in _fnames:
            raise ValueError(
                f"Unknown model '{model_name}'. "
                f"Choose from: {list(_fnames.keys())}"
            )
        fname = model_file_name or _fnames[name]

        if name == "arima":
            return self.train_arima(
                order=params.get("order", (1, 1, 1)),
                model_file_name=fname,
            )
        if name == "sarima":
            return self.train_sarima(
                order=params.get("order", (1, 1, 1)),
                seasonal_order=params.get("seasonal_order", (1, 1, 1, 12)),
                model_file_name=fname,
            )
        if name == "prophet":
            return self.train_prophet(
                changepoint_prior_scale=params.get("changepoint_prior_scale", 0.05),
                seasonality_mode=params.get("seasonality_mode", "additive"),
                model_file_name=fname,
            )
        if name == "lstm":
            return self.train_lstm(
                units_1=params.get("units_1", 64),
                units_2=params.get("units_2", 32),
                dropout=params.get("dropout", 0.2),
                epochs=params.get("epochs", 100),
                batch_size=params.get("batch_size", 16),
                patience=params.get("patience", 15),
                model_file_name=fname,
            )