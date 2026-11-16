import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# handles forecasting for all models
class Forecaster:

    # initializes forecaster
    def __init__(
        self,
        full_series: pd.Series,
        scaler,
        look_back: int = 12,
        freq: str = "ME",
        output_dir: str = "./Forecasts",
    ):
        if not isinstance(full_series.index, pd.DatetimeIndex):
            raise TypeError("full_series must have a DatetimeIndex.")

        self.series = full_series
        self.scaler = scaler
        self.look_back = look_back
        self.freq = freq
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # creates future datetime index
    def _future_index(self, n: int) -> pd.DatetimeIndex:
        offset = pd.tseries.frequencies.to_offset(self.freq)
        return pd.date_range(
            start = self.series.index[-1] + offset,
            periods = n,
            freq = self.freq,
        )

    # forecasts using arima or sarima
    def forecast_arima(
        self,
        fitted_model,
        n_steps: int,
        model_name: str = "ARIMA",
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        print(f"\n  {model_name}: forecasting {n_steps} steps …")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc     = fitted_model.get_forecast(steps=n_steps)
            summary = fc.summary_frame(alpha=alpha)

        idx = self._future_index(n_steps)
        result = pd.DataFrame(
            {
                "forecast":  summary["mean"].values,
                "lower_ci":  summary["mean_ci_lower"].values,
                "upper_ci":  summary["mean_ci_upper"].values,
            },
            index=idx,
        )
        result.index.name = "Date"
        print(f" {result['forecast'].round(2).values.tolist()}")
        return result

    # forecasts using prophet
    def forecast_prophet(
        self,
        prophet_model,
        n_steps: int,
        model_name: str = "Prophet",
    ) -> pd.DataFrame:
        print(f"\n  {model_name}: forecasting {n_steps} steps …")
        try:
            future = prophet_model.make_future_dataframe(
                periods=n_steps, freq=self.freq
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fc = prophet_model.predict(future)

            result = (
                fc[["ds", "yhat", "yhat_lower", "yhat_upper"]]
                .tail(n_steps)
                .rename(columns={
                    "ds":          "Date",
                    "yhat":        "forecast",
                    "yhat_lower":  "lower_ci",
                    "yhat_upper":  "upper_ci",
                }).set_index("Date")
            )
            result.index = self._future_index(n_steps)
            print(f" {result['forecast'].round(2).values.tolist()}")
            return result
        except Exception as exc:
            print(f"  [WARN] Prophet forecast failed: {exc}")
            return pd.DataFrame()

    # forecasts using lstm
    def forecast_lstm(
        self,
        lstm_model,
        n_steps: int,
        model_name: str = "LSTM",
    ) -> pd.DataFrame:
        print(f"\n  {model_name}: forecasting {n_steps} steps …")

        last_values = self.series.values[-self.look_back:]
        last_scaled = self.scaler.transform(
            last_values.reshape(-1, 1)
        ).flatten()

        history   = list(last_scaled)
        forecasts = []

        for _ in range(n_steps):
            seq  = np.array(history[-self.look_back:]).reshape(1, self.look_back, 1)
            pred = float(lstm_model.predict(seq, verbose=0)[0, 0])
            forecasts.append(pred)
            history.append(pred)

        preds_original = self.scaler.inverse_transform(
            np.array(forecasts).reshape(-1, 1)
        ).flatten()

        idx = self._future_index(n_steps)
        result = pd.DataFrame({"forecast": preds_original}, index=idx)
        result.index.name = "Date"
        print(f"{result['forecast'].round(2).values.tolist()}")
        return result

    # plots combined forecasts
    def plot_all_forecasts(
        self,
        forecasts: dict,
        n_history: int = 36,
        title: str = "WQI Multi-Model Future Forecast"):
        history = self.series.iloc[-min(n_history, len(self.series)):]

        fig, ax = plt.subplots(figsize=(16, 6))
        ax.plot(history.index, history.values,
                color="steelblue", linewidth=2, label="Historical Risk_Score")

        ax.axvline(x=self.series.index[-1], color="gray",
                   linestyle=":", linewidth=1.5, label="Forecast Start")

        colors = ["tomato", "green", "darkorange", "purple", "sienna"]
        for (name, fc_df), color in zip(forecasts.items(), colors):
            if fc_df is None or (isinstance(fc_df, pd.DataFrame) and fc_df.empty):
                continue
            fc_vals = (fc_df["forecast"] if isinstance(fc_df, pd.DataFrame)
                       else fc_df)
            ax.plot(fc_vals.index, fc_vals.values,
                    label=name, linestyle="--", linewidth=2, color=color,
                    marker="o", markersize=4)
            if isinstance(fc_df, pd.DataFrame) and "lower_ci" in fc_df.columns:
                ax.fill_between(
                    fc_df.index,
                    fc_df["lower_ci"], fc_df["upper_ci"],
                    alpha=0.12, color=color,
                )

        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Date"); ax.set_ylabel("Risk_Score")
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "multi_model_forecast.png"),
                    dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Combined forecast chart saved.")

    # plots single forecast
    def plot_single_forecast(
        self, name: str, fc_df: pd.DataFrame, n_history: int = 36
    ):
        history  = self.series.iloc[-min(n_history, len(self.series)):]
        fc_vals  = fc_df["forecast"]

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(history.index, history.values, color="steelblue",
                linewidth=1.8, label="History")
        ax.plot(fc_vals.index, fc_vals.values, color="tomato",
                linewidth=2, linestyle="--", marker="o",
                markersize=5, label="Forecast")

        if "lower_ci" in fc_df.columns:
            ax.fill_between(fc_df.index, fc_df["lower_ci"], fc_df["upper_ci"],
                            alpha=0.15, color="tomato", label="95 % CI")

        ax.axvline(x=self.series.index[-1], color="gray",
                   linestyle=":", linewidth=1.5)
        ax.set_title(f"{name} — {len(fc_vals)}-Step Forecast", fontsize=13)
        ax.set_xlabel("Date"); ax.set_ylabel("Risk_Score")
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir,
                         f"{name.replace(' ', '_')}_forecast_detail.png"),
            dpi=150,
        )
        plt.close()

    # saves forecasts to csv
    def save_forecasts(self, forecasts: dict):
        rows = []
        for name, fc_df in forecasts.items():
            if fc_df is None or (isinstance(fc_df, pd.DataFrame) and fc_df.empty):
                continue
            df_out = (fc_df[["forecast"]].copy()
                      if isinstance(fc_df, pd.DataFrame) else
                      fc_df.to_frame("forecast"))
            df_out["model"] = name
            rows.append(df_out)
        if rows:
            path = os.path.join(self.output_dir, "all_forecasts.csv")
            pd.concat(rows).to_csv(path)
            print(f"  All forecasts saved → {path}")

    # runs full forecasting pipeline
    def run_forecast(
        self,
        n_steps: int = 12,
        arima_model=None,
        sarima_model=None,
        prophet_model=None,
        lstm_model=None,
    ) -> dict:
        print(f"\nForecasting {n_steps} steps ahead")
        all_forecasts = {}

        if arima_model is not None:
            all_forecasts["ARIMA"] = self.forecast_arima(
                arima_model, n_steps, model_name="ARIMA"
            )
        if sarima_model is not None:
            all_forecasts["SARIMA"] = self.forecast_arima(
                sarima_model, n_steps, model_name="SARIMA"
            )
        if prophet_model is not None:
            all_forecasts["Prophet"] = self.forecast_prophet(
                prophet_model, n_steps, model_name="Prophet"
            )
        if lstm_model is not None:
            all_forecasts["LSTM"] = self.forecast_lstm(
                lstm_model, n_steps, model_name="LSTM"
            )

        if all_forecasts:
            self.plot_all_forecasts(all_forecasts)
            for name, fc_df in all_forecasts.items():
                if fc_df is not None and not (
                    isinstance(fc_df, pd.DataFrame) and fc_df.empty
                ):
                    self.plot_single_forecast(name, fc_df)
            self.save_forecasts(all_forecasts)

        print(f"\n Forecasting completed ({n_steps} steps ahead).\n")
        return all_forecasts