import warnings
import itertools
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

try:
    _TF_OK = True
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import MinMaxScaler
except ImportError:
    _TF_OK = False


# performs hyperparameter optimization
class TimeSeriesHPO:

    # initializes hpo class
    def __init__(
        self,
        series: pd.Series,
        n_splits: int = 5,
    ):
        if not isinstance(series.index, pd.DatetimeIndex):
            raise TypeError("series must have a DatetimeIndex.")
        self.series = series.sort_index()
        self.n_splits = n_splits

    # computes rmse metric
    @staticmethod
    def _rmse(y_true, y_pred) -> float:
        return float(np.sqrt(np.mean((np.asarray(y_true) -
                                      np.asarray(y_pred)) ** 2)))

    # searches best arima order
    def arima_order_search(
        self,
        p_range: range = range(0, 4),
        d_range: range = range(0, 3),
        q_range: range = range(0, 4),
    ) -> dict:
        print(f"\n  ARIMA order search  "
              f"(p∈{list(p_range)}, d∈{list(d_range)}, q∈{list(q_range)}) …")

        best_aic = np.inf
        best_order = None
        results = []

        for p, d, q in itertools.product(p_range, d_range, q_range):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = ARIMA(self.series, order=(p, d, q)).fit()
                results.append({"p": p, "d": d, "q": q, "AIC": round(m.aic, 4)})
                if m.aic < best_aic:
                    best_aic = m.aic
                    best_order = (p, d, q)
            except Exception:
                pass

        df = pd.DataFrame(results).sort_values("AIC")
        print(f"  Best ARIMA order: {best_order}   AIC={best_aic:.2f}")
        print(df.head(10).to_string(index=False))
        return {"best_order": best_order, "best_aic": best_aic, "results": df}

    # searches best sarima order
    def sarima_order_search(
        self,
        p_range: range = range(0, 3),
        d_range: range = range(0, 2),
        q_range: range = range(0, 3),
        P_range: range = range(0, 2),
        D_range: range = range(0, 2),
        Q_range: range = range(0, 2),
        s: int = 12,
    ) -> dict:
        print(f"\n  SARIMA order search  (s={s}) …")
        best_aic   = np.inf
        best_order = None
        best_so    = None
        results    = []

        for p, d, q, P, D, Q in itertools.product(
            p_range, d_range, q_range, P_range, D_range, Q_range
        ):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = SARIMAX(
                        self.series,
                        order=(p, d, q),
                        seasonal_order=(P, D, Q, s),
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit(disp=False)
                results.append({
                    "p": p, "d": d, "q": q,
                    "P": P, "D": D, "Q": Q,
                    "AIC": round(m.aic, 4),
                })
                if m.aic < best_aic:
                    best_aic   = m.aic
                    best_order = (p, d, q)
                    best_so    = (P, D, Q, s)
            except Exception:
                pass

        df = pd.DataFrame(results).sort_values("AIC")
        print(f"  Best SARIMA: {best_order} × {best_so}   AIC={best_aic:.2f}")
        print(df.head(10).to_string(index=False))
        return {
            "best_order":          best_order,
            "best_seasonal_order": best_so,
            "best_aic":            best_aic,
            "results":             df,
        }

    # searches best lstm parameters
    def lstm_param_search(
        self,
        look_back: int = 12,
        units_list: list = None,
        dropout_list: list = None,
        batch_list: list = None,
        epochs: int = 40,
    ) -> dict:
        if not _TF_OK:
            print("  [SKIP] TensorFlow not installed.")
            return {}

        units_list   = units_list   or [(32, 16), (64, 32), (128, 64)]
        dropout_list = dropout_list or [0.1, 0.2]
        batch_list   = batch_list   or [8, 16]

        values = self.series.values
        tscv   = TimeSeriesSplit(n_splits=self.n_splits)
        results = []

        print(f"\n  LSTM param search  "
              f"(units={units_list}, dropout={dropout_list}, "
              f"batch={batch_list}) …")

        for (u1, u2), dr, bs in itertools.product(
            units_list, dropout_list, batch_list
        ):
            fold_rmses = []
            for tr_idx, te_idx in tscv.split(values):
                y_tr = values[tr_idx]
                y_te = values[te_idx]
                if len(y_tr) <= look_back:
                    continue

                sc = MinMaxScaler(feature_range=(0, 1))
                y_tr_sc = sc.fit_transform(
                    y_tr.reshape(-1, 1)
                ).flatten()

                from Step_3_Data_Preparation import DataPreparation
                X_tr, y_tr_seq = DataPreparation.create_sequences(
                    y_tr_sc, look_back
                )
                if len(X_tr) == 0:
                    continue

                model = Sequential([
                    LSTM(u1, return_sequences=True,
                         input_shape=(look_back, 1)),
                    Dropout(dr),
                    LSTM(u2, return_sequences=False),
                    Dropout(dr),
                    Dense(1),
                ])
                model.compile(optimizer="adam", loss="mse")
                model.fit(
                    X_tr, y_tr_seq,
                    epochs=epochs, batch_size=bs,
                    validation_split=0.1,
                    callbacks=[EarlyStopping(patience=8,
                                             restore_best_weights=True)],
                    verbose=0,
                )

                history = list(y_tr_sc)
                preds   = []
                for i in range(len(y_te)):
                    seq  = np.array(history[-look_back:]).reshape(1, look_back, 1)
                    p_sc = float(model.predict(seq, verbose=0)[0, 0])
                    preds.append(p_sc)
                    history.append(
                        sc.transform([[y_te[i]]])[0, 0]
                    )

                y_pred = sc.inverse_transform(
                    np.array(preds).reshape(-1, 1)
                ).flatten()
                fold_rmses.append(self._rmse(y_te, y_pred))
                tf.keras.backend.clear_session()

            if fold_rmses:
                avg_rmse = float(np.mean(fold_rmses))
                results.append({
                    "units_1": u1, "units_2": u2,
                    "dropout": dr, "batch_size": bs,
                    "CV_RMSE": round(avg_rmse, 4),
                })
                print(f"u=({u1},{u2}) dr={dr} bs={bs}  "
                      f"→ CV RMSE={avg_rmse:.4f}")

        df = pd.DataFrame(results).sort_values("CV_RMSE")
        best = df.iloc[0].to_dict() if not df.empty else {}
        print(f"\n  Best LSTM params: {best}")
        return {"best_params": best, "results": df}