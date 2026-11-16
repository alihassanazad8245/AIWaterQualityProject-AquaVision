import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

try:
    _TF_OK = True
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping
except ImportError:
    _TF_OK = False


# performs walk forward cross validation
class WalkForwardCV:

    # initializes cross validation
    def __init__(self, series: pd.Series, n_splits: int = 5):
        if not isinstance(series.index, pd.DatetimeIndex):
            raise TypeError("series must have a DatetimeIndex.")
        self.series   = series.sort_index()
        self.n_splits = n_splits
        self.results: list = []

    # computes evaluation metrics
    @staticmethod
    def _metrics(y_true, y_pred) -> dict:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        mae  = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mask = y_true != 0
        mape = (float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)if mask.sum() > 0 else float("nan"))
        return {"MAE": round(mae, 4), "RMSE": round(rmse, 4),
                "MAPE": round(mape, 2) if not np.isnan(mape) else float("nan")}

    # performs arima walk forward validation
    def cv_arima(self, order: tuple = (1, 1, 1)) -> pd.DataFrame:
        print(f"\n  Walk-Forward CV — ARIMA{order}  ({self.n_splits} folds)")
        self.results = []
        values = self.series.values
        tscv = TimeSeriesSplit(n_splits=self.n_splits)

        for fold, (tr_idx, te_idx) in enumerate(tscv.split(values), start=1):
            y_tr = values[tr_idx]
            y_te = values[te_idx]

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = ARIMA(y_tr, order=order).fit()
                y_pred = m.forecast(steps=len(y_te))
            except Exception as exc:
                print(f"Fold {fold} failed: {exc}")
                continue

            row = {"Fold": fold, "Train_size": len(y_tr),"Test_size": len(y_te)}
            row.update(self._metrics(y_te, y_pred))
            self.results.append(row)
            print(f"Fold {fold:2d} │ RMSE={row['RMSE']:.4f}  "
                  f"MAE={row['MAE']:.4f}  MAPE={row['MAPE']:.2f}%")

        return pd.DataFrame(self.results)

    # performs sarima walk forward validation
    def cv_sarima(
        self,
        order: tuple = (1, 1, 1),
        seasonal_order: tuple = (1, 1, 1, 12),
    ) -> pd.DataFrame:
        print(f"\n  Walk-Forward CV — SARIMA{order}×{seasonal_order}  "
              f"({self.n_splits} folds)")
        self.results = []
        values = self.series.values
        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        s = seasonal_order[3]

        for fold, (tr_idx, te_idx) in enumerate(
            tscv.split(values), start=1
        ):
            y_tr = values[tr_idx]
            y_te = values[te_idx]

            if len(y_tr) < 2 * s:
                print(f"    Fold {fold} skipped (train too short for s={s}).")
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = SARIMAX(
                        y_tr, order=order,
                        seasonal_order=seasonal_order,
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit(disp=False)
                y_pred = m.forecast(steps=len(y_te))
            except Exception as exc:
                print(f" Fold {fold} failed: {exc}")
                continue

            row = {"Fold": fold, "Train_size": len(y_tr),
                   "Test_size": len(y_te)}
            row.update(self._metrics(y_te, y_pred))
            self.results.append(row)
            print(f"    Fold {fold:2d} │ RMSE={row['RMSE']:.4f}  "
                  f"MAE={row['MAE']:.4f}  MAPE={row['MAPE']:.2f}%")

        return pd.DataFrame(self.results)

    # performs lstm walk forward validation
    def cv_lstm(
        self,
        scaler,
        look_back: int = 12,
        units_1: int = 64,
        units_2: int = 32,
        dropout: float = 0.2,
        epochs: int = 50,
        batch_size: int = 16,
    ) -> pd.DataFrame:
        if not _TF_OK:
            print("  [SKIP] TensorFlow not installed.")
            return pd.DataFrame()

        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout

        print(f"\n  Walk-Forward CV — LSTM  ({self.n_splits} folds)")
        self.results = []
        values = self.series.values
        tscv   = TimeSeriesSplit(n_splits=self.n_splits)

        for fold, (tr_idx, te_idx) in enumerate(
            tscv.split(values), start=1
        ):
            y_tr_raw = values[tr_idx]
            y_te_raw = values[te_idx]

            if len(y_tr_raw) <= look_back:
                print(f"    Fold {fold} skipped (train too short).")
                continue

            fold_scaler = type(scaler)(feature_range=(0, 1))
            y_tr_scaled = fold_scaler.fit_transform(
                y_tr_raw.reshape(-1, 1)
            ).flatten()

            from Step_3_Data_Preparation import DataPreparation
            X_tr, y_tr = DataPreparation.create_sequences(
                y_tr_scaled, look_back
            )

            if len(X_tr) == 0:
                continue

            model = Sequential([
                LSTM(units_1, return_sequences=True,input_shape=(look_back, 1)),
                Dropout(dropout),
                LSTM(units_2, return_sequences=False),
                Dropout(dropout),
                Dense(1),
            ])
            model.compile(optimizer="adam", loss="mse")
            model.fit(
                X_tr, y_tr,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.1,
                callbacks=[EarlyStopping(patience=10, restore_best_weights=True)],
                verbose=0,
            )

            history = list(y_tr_scaled)
            preds   = []
            for _ in range(len(y_te_raw)):
                seq   = np.array(history[-look_back:]).reshape(1, look_back, 1)
                p_sc  = float(model.predict(seq, verbose=0)[0, 0])
                preds.append(p_sc)
                true_sc = fold_scaler.transform(
                    [[y_te_raw[len(preds) - 1]]]
                )[0, 0]
                history.append(true_sc)

            y_pred = fold_scaler.inverse_transform(
                np.array(preds).reshape(-1, 1)
            ).flatten()

            row = {"Fold": fold, "Train_size": len(y_tr_raw),
                   "Test_size": len(y_te_raw)}
            row.update(self._metrics(y_te_raw, y_pred))
            self.results.append(row)
            print(f"    Fold {fold:2d} │ RMSE={row['RMSE']:.4f}  "
                  f"MAE={row['MAE']:.4f}  MAPE={row['MAPE']:.2f}%")

            tf.keras.backend.clear_session()

        return pd.DataFrame(self.results)

    # summarizes cross validation results
    def summary(self, model_name: str = "") -> pd.DataFrame:
        if not self.results:
            print("  No results to summarise.")
            return pd.DataFrame()

        df = pd.DataFrame(self.results)
        print(f"\nWalk-Forward CV Summary — {model_name}")
        for m in ["RMSE", "MAE", "MAPE"]:
            if m in df.columns:
                v = df[m].dropna()
                print(f"    {m:5s}  mean={v.mean():.4f}   std={v.std():.4f}")
        print("  ──────────────────────────────────────────────────────")
        return df