import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm as sp_norm
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


# Performs exploratory data analysis on a time series DataFrame
class TimeSeriesEDA:

    # Initialises EDA with target column and output directory
    def __init__(self, ts_df, target_col="Risk_Score", output_dir="./EDA"):
        self.ts_df = ts_df.copy()
        self.target_col = target_col
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.stationarity_results: dict = {}

    # Returns full file path for a given output filename
    def _fp(self, name: str):
        return os.path.join(self.output_dir, name)

    # Saves and closes the current matplotlib figure
    def _save(self, name):
        plt.tight_layout()
        plt.savefig(self._fp(name), dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved to {name}")

    # Returns the target series with NaNs dropped, or None (with a log message) if unusable
    def _clean_series(self, min_points: int = 1):
        if self.target_col not in self.ts_df.columns:
            print(f"  [SKIP] Column '{self.target_col}' not found in ts_df.")
            return None
        series = self.ts_df[self.target_col].dropna()
        if len(series) < min_points:
            print(f"  [SKIP] '{self.target_col}' has only {len(series)} non-null point(s) "
                  f"(need ≥{min_points}). Check upstream resampling/date parsing — "
                  f"sparse source data can collapse to almost nothing after resampling.")
            return None
        return series

    # Plots the full raw Risk_Score time series
    def plot_raw_series(self):
        series = self._clean_series(min_points=1)
        if series is None:
            return
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.plot(series.index, series.values, color="steelblue", linewidth=1.5)
        ax.set_title(f"{self.target_col} — Full Time Series", fontsize=14)
        ax.set_xlabel("Date"); ax.set_ylabel(self.target_col)
        ax.grid(alpha=0.3)
        self._save("01_raw_time_series.png")

    # Plots rolling mean and standard deviation for multiple window sizes
    def plot_rolling_statistics(self, windows=(3, 6, 12)):
        series = self._clean_series(min_points=2)
        if series is None:
            return
        # Only use windows that are actually smaller than the series length
        usable_windows = [w for w in windows if w < len(series)]
        if not usable_windows:
            print(f"  [SKIP] Rolling statistics need a series longer than the smallest "
                  f"window ({min(windows)}); series has {len(series)} points.")
            return
        fig, axes = plt.subplots(len(usable_windows), 1,
                                  figsize=(14, 4 * len(usable_windows)), sharex=True)
        if len(usable_windows) == 1:
            axes = [axes]
        for ax, w in zip(axes, usable_windows):
            rm = series.rolling(w).mean()
            rs = series.rolling(w).std()
            ax.plot(series, color="steelblue", alpha=0.45, linewidth=1, label="Actual")
            ax.plot(rm, color="darkorange", linewidth=2, label=f"Rolling Mean (w={w})")
            ax.fill_between(series.index, rm - rs, rm + rs, alpha=0.15, color="darkorange", label=f"±1 Std (w={w})")
            ax.set_title(f"Rolling window = {w} periods", fontsize=11)
            ax.legend(fontsize=8); ax.grid(alpha=0.25)
        plt.suptitle(f"Rolling Statistics — {self.target_col}", fontsize=13)
        self._save("02_rolling_statistics.png")

    # Decomposes time series into trend, seasonal, and residual components
    def plot_decomposition(self, period=12):
        series = self._clean_series(min_points=1)
        if series is None:
            return
        if len(series) < 2 * period:
            print(f"[SKIP] Decomposition needs ≥{2*period} periods (have {len(series)}).")
            return
        if series.nunique() <= 1:
            print(f"[SKIP] '{self.target_col}' is constant — decomposition is undefined.")
            return

        for model_type in ("additive", "multiplicative"):
            try:
                decomp = seasonal_decompose(
                    series, model=model_type, period=period,
                    extrapolate_trend="freq"
                )
                fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
                for ax, data, title, color in zip(
                    axes,
                    [series, decomp.trend, decomp.seasonal, decomp.resid],
                    ["Observed", "Trend", "Seasonal", "Residual"],
                    ["steelblue", "darkorange", "green", "tomato"],
                ):
                    ax.plot(data, color=color, linewidth=1.2)
                    ax.set_title(title, fontsize=11)
                    ax.grid(alpha=0.25)
                plt.suptitle(
                    f"Seasonal Decomposition ({model_type.title()}, period={period})",
                    fontsize=13,
                )
                self._save(f"03_decomposition_{model_type}.png")
            except Exception as exc:
                print(f"  [WARN] {model_type} decomposition failed: {exc}")

    # Runs ADF and KPSS stationarity tests and saves results
    def test_stationarity(self):
        series = self._clean_series(min_points=1)
        if series is None:
            self.stationarity_results = {}
            return self.stationarity_results

        if series.nunique() <= 1 or np.isclose(series.std(), 0):
            print(f"  [SKIP] '{self.target_col}' is constant (nunique={series.nunique()}) "
                  f"— ADF/KPSS are undefined for a constant series. This usually means the "
                  f"underlying data is too sparse for the resampling frequency you're using "
                  f"(check date parsing / fill method upstream).")
            self.stationarity_results = {
                "ADF": {"Statistic": None, "p_value": None, "Stationary": None, "note": "constant series"},
                "KPSS": {"Statistic": None, "p_value_approx": None, "Stationary": None, "note": "constant series"},
            }
            pd.DataFrame(self.stationarity_results).T.to_csv(self._fp("04_stationarity_results.csv"))
            return self.stationarity_results

        if len(series) < 8:
            print(f"  [SKIP] '{self.target_col}' has only {len(series)} points — too few for "
                  f"reliable ADF/KPSS testing (need at least ~8-12).")
            self.stationarity_results = {
                "ADF": {"Statistic": None, "p_value": None, "Stationary": None, "note": "insufficient data"},
                "KPSS": {"Statistic": None, "p_value_approx": None, "Stationary": None, "note": "insufficient data"},
            }
            pd.DataFrame(self.stationarity_results).T.to_csv(self._fp("04_stationarity_results.csv"))
            return self.stationarity_results

        try:
            adf_stat, adf_p, _, _, adf_crit, _ = adfuller(series, autolag="AIC")
            adf_ok = bool(adf_p < 0.05)
        except Exception as exc:
            print(f"  [WARN] ADF test failed: {exc}")
            adf_stat = adf_p = None
            adf_crit = {"1%": None, "5%": None}
            adf_ok = None

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kpss_stat, kpss_p, _, kpss_crit = kpss(series, regression="c", nlags="auto")
            kpss_ok = bool(kpss_p > 0.05)
        except Exception as exc:
            print(f"  [WARN] KPSS test failed: {exc}")
            kpss_stat = kpss_p = None
            kpss_crit = {"5%": None}
            kpss_ok = None

        self.stationarity_results = {
            "ADF": {
                "Statistic":     round(adf_stat, 4) if adf_stat is not None else None,
                "p_value":       round(adf_p, 4) if adf_p is not None else None,
                "Critical_1pct": adf_crit.get("1%"),
                "Critical_5pct": adf_crit.get("5%"),
                "Stationary":    adf_ok,
            },
            "KPSS": {
                "Statistic":      round(kpss_stat, 4) if kpss_stat is not None else None,
                "p_value_approx": round(kpss_p, 4) if kpss_p is not None else None,
                "Critical_5pct":  kpss_crit.get("5%"),
                "Stationary":     kpss_ok,
            },
        }

        print("\n── Stationarity Tests ─────────────────────────────────────")
        if adf_stat is not None:
            print(f"  ADF  │ stat={adf_stat:8.4f}  p={adf_p:.4f}  "
                  f"→ {'Stationary ' if adf_ok  else 'Non-stationary ✗'}")
        if kpss_stat is not None:
            print(f"  KPSS │ stat={kpss_stat:8.4f}  p≈{kpss_p:.4f}  "
                  f"→ {'Stationary ' if kpss_ok else 'Non-stationary ✗'}")
        print("───────────────────────────────────────────────────────────")

        pd.DataFrame(self.stationarity_results).T.to_csv(self._fp("04_stationarity_results.csv"))
        return self.stationarity_results

    # Plots ACF and PACF to assist with ARIMA order selection
    def plot_acf_pacf(self, lags: int = 24):
        series = self._clean_series(min_points=3)
        if series is None:
            return

        max_lags = min(lags, len(series) // 2 - 1)
        if max_lags < 1:
            print(f"  [SKIP] Not enough points for ACF/PACF (have {len(series)}, "
                  f"need ≥{2*1 + 2} for even a single lag).")
            return
        if series.nunique() <= 1:
            print(f"  [SKIP] '{self.target_col}' is constant — ACF/PACF are undefined.")
            return

        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        plot_acf(series,  lags=max_lags, ax=axes[0], title="ACF")
        plot_pacf(series, lags=max_lags, ax=axes[1], title="PACF", method="ywm")
        plt.suptitle("ACF & PACF ", fontsize=12)
        self._save("05_acf_pacf.png")

    # Plots correlation heatmap of all numeric features
    def plot_feature_correlations(self):
        num_df = self.ts_df.select_dtypes(include=np.number)
        if num_df.shape[1] < 2:
            print("  [SKIP] Need ≥2 numeric columns for a correlation heatmap.")
            return
        if num_df.dropna(how="all").empty:
            print("  [SKIP] No numeric data available for correlation heatmap.")
            return
        plt.figure(figsize=(16, 12))
        sns.heatmap(num_df.corr(), annot=True, fmt=".2f",
                    cmap="coolwarm", annot_kws={"size": 7})
        plt.title("Feature Correlation Heatmap — Resampled TS", fontsize=13)
        self._save("06_feature_correlations.png")

    # Plots Risk_Score histogram and boxplot to inspect distribution shape
    def plot_target_distribution(self):
        series = self._clean_series(min_points=2)
        if series is None:
            return
        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        axes[0].hist(series, bins=min(30, max(1, series.nunique())),
                     color="steelblue", edgecolor="white", alpha=0.85, density=True)
        if series.nunique() > 1:
            try:
                mu, sd = sp_norm.fit(series)
                x_fit  = np.linspace(series.min(), series.max(), 200)
                if sd > 0:
                    axes[0].plot(x_fit, sp_norm.pdf(x_fit, mu, sd), "r-", linewidth=2,
                                 label=f"Normal fit  μ={mu:.1f}  σ={sd:.1f}")
                    axes[0].legend()
            except Exception as exc:
                print(f"  [WARN] Normal fit failed: {exc}")
        axes[0].set_title(f"{self.target_col} Distribution")
        axes[1].boxplot(series, vert=False, patch_artist=True,
                        boxprops=dict(facecolor="steelblue", alpha=0.6))
        axes[1].set_title(f"{self.target_col} Boxplot")
        plt.suptitle("Risk_Score Distribution Analysis", fontsize=13)
        self._save("07_Risk_Score_distribution.png")

    # Plots a year-by-month heatmap of average Risk_Score values
    def plot_calendar_heatmap(self):
        series = self._clean_series(min_points=1)
        if series is None:
            return
        if not isinstance(series.index, pd.DatetimeIndex):
            print("  [SKIP] Calendar heatmap needs a DatetimeIndex.")
            return
        cal = pd.DataFrame({
            "Year":  series.index.year,
            "Month": series.index.month,
            "Value": series.values,
        })
        pivot = cal.pivot_table(index="Year", columns="Month", values="Value", aggfunc="mean")
        if pivot.shape[0] < 2:
            print("  [SKIP] Calendar heatmap needs ≥2 years.")
            return
        month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                        "Jul","Aug","Sep","Oct","Nov","Dec"]
        pivot.columns = [month_labels[m - 1] for m in pivot.columns]
        plt.figure(figsize=(14, max(4, pivot.shape[0] * 1.2)))
        sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd",
                    linewidths=0.5, linecolor="white")
        plt.title(f"{self.target_col} Calendar Heatmap (Year × Month)", fontsize=13)
        self._save("08_calendar_heatmap.png")

    # Plots monthly Risk_Score values per year for year-over-year comparison
    def plot_yoy_comparison(self):
        series = self._clean_series(min_points=1)
        if series is None:
            return
        if not isinstance(series.index, pd.DatetimeIndex):
            print("  [SKIP] YoY comparison needs a DatetimeIndex.")
            return
        df_yoy = pd.DataFrame({
            "Year":  series.index.year,
            "Month": series.index.month,
            "Risk_Score":   series.values,
        })
        years = df_yoy["Year"].unique()
        if len(years) < 2:
            print("  [SKIP] YoY comparison needs ≥2 years.")
            return
        fig, ax = plt.subplots(figsize=(13, 5))
        palette = plt.cm.tab10(np.linspace(0, 1, len(years)))
        for year, color in zip(sorted(years), palette):
            sub = df_yoy[df_yoy["Year"] == year].sort_values("Month")
            ax.plot(sub["Month"], sub["Risk_Score"], marker="o", label=str(year),
                    linewidth=1.6, color=color)
        ax.set_title("Year-over-Year Risk_Score Comparison", fontsize=13)
        ax.set_xlabel("Month"); ax.set_ylabel("Risk_Score")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun",
                             "Jul","Aug","Sep","Oct","Nov","Dec"])
        ax.legend(title="Year", fontsize=8); ax.grid(alpha=0.3)
        self._save("09_yoy_comparison.png")

    # Plots boxplots of Risk_Score grouped by month to reveal seasonal patterns
    def plot_monthly_boxplots(self):
        series = self._clean_series(min_points=1)
        if series is None:
            return
        if not isinstance(series.index, pd.DatetimeIndex):
            print("  [SKIP] Monthly boxplots need a DatetimeIndex.")
            return
        df_box = pd.DataFrame({
            "Month": series.index.month_name(),
            "Risk_Score":   series.values,
        })
        month_order = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]
        df_box["Month"] = pd.Categorical(df_box["Month"], categories=month_order, ordered=True)
        if df_box["Month"].nunique(dropna=True) < 2:
            print("  [SKIP] Monthly boxplots need data spanning ≥2 distinct months.")
            return
        fig, ax = plt.subplots(figsize=(14, 5))
        sns.boxplot(data=df_box, x="Month", y="Risk_Score", palette="Set3", ax=ax)
        ax.set_title("Monthly Risk_Score Distribution  (Seasonality Check)", fontsize=13)
        ax.set_xlabel("Month"); ax.set_ylabel("Risk_Score")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.3)
        self._save("10_monthly_boxplots.png")

    # Plots trend lines for all physicochemical parameters over time
    def plot_parameter_trends(self):
        params = [
            'pH', 'Turbidity (NTU)', 'EC (µS/cm)',
            'TDS (mg/L)', 'Hardness (mg/L)',
            'Calcium (mg/L)', 'Magnesium (mg/L)',
            'Sodium (mg/L)', 'Potassium (mg/L)',
            'Chloride (mg/L)', 'Sulfate (mg/L)',
            'Nitrate (mg/L)', 'Fluoride (mg/L)',
            'Iron (mg/L)', 'Arsenic (mg/L)', 'Total Coliform', 'E. Coli'
        ]
        available = [p for p in params if p in self.ts_df.columns
                     and self.ts_df[p].notna().sum() > 0]
        if not available:
            print("  [SKIP] No physicochemical parameter columns with data found.")
            return
        n_cols = 3
        n_rows = (len(available) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 4 * n_rows), sharex=True)
        axes = np.atleast_1d(axes).flatten()
        for ax, col in zip(axes, available):
            ax.plot(self.ts_df.index, self.ts_df[col], color="steelblue", linewidth=1.2)
            valid_n = self.ts_df[col].notna().sum()
            window = min(6, max(1, valid_n))
            if window > 1:
                rm = self.ts_df[col].rolling(window).mean()
                ax.plot(self.ts_df.index, rm, color="tomato", linewidth=1.5,
                        linestyle="--", label=f"{window}-period MA")
                ax.legend(fontsize=7)
            ax.set_title(col, fontsize=10)
            ax.grid(alpha=0.25)
        for ax in axes[len(available):]:
            ax.set_visible(False)
        plt.suptitle("Physicochemical Parameter Trends Over Time", fontsize=14)
        self._save("11_parameter_trends.png")

    # Plots scatter charts of Risk_Score against key physicochemical parameters
    def plot_Risk_Score_vs_parameters(self):
        if self.target_col not in self.ts_df.columns:
            print(f"  [SKIP] Column '{self.target_col}' not found in ts_df.")
            return
        key_params = [
            'pH', 'Turbidity (NTU)', 'EC (µS/cm)',
            'TDS (mg/L)', 'Hardness (mg/L)',
            'Calcium (mg/L)', 'Magnesium (mg/L)',
            'Sodium (mg/L)', 'Potassium (mg/L)',
            'Chloride (mg/L)', 'Sulfate (mg/L)',
            'Nitrate (mg/L)', 'Fluoride (mg/L)',
            'Iron (mg/L)', 'Arsenic (mg/L)', 'Total Coliform', 'E. Coli'
        ]
        available = [p for p in key_params if p in self.ts_df.columns
                     and self.ts_df[[p, self.target_col]].dropna(how="any").shape[0] > 1]
        if not available:
            print("  [SKIP] No parameter columns with enough overlapping (non-null) "
                  "data against the target column.")
            return
        n_cols = 3
        n_rows = (len(available) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 5 * n_rows))
        axes = np.atleast_1d(axes).flatten()
        for ax, col in zip(axes, available):
            pair = self.ts_df[[col, self.target_col]].dropna()
            x, y = pair[col], pair[self.target_col]
            ax.scatter(x, y, alpha=0.5, color="steelblue", s=30)
            if len(x) > 2 and x.nunique() > 1:
                try:
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    x_sorted = sorted(x)
                    ax.plot(x_sorted, p(x_sorted), "r--", linewidth=1.5, label="Trend")
                    ax.legend(fontsize=7)
                except Exception as exc:
                    print(f"  [WARN] Trend fit failed for {col}: {exc}")
            ax.set_xlabel(col); ax.set_ylabel("Risk_Score")
            ax.set_title(f"Risk_Score vs {col}", fontsize=10)
            ax.grid(alpha=0.25)
        for ax in axes[len(available):]:
            ax.set_visible(False)
        plt.suptitle("Risk_Score vs Key Physicochemical Parameters", fontsize=13)
        self._save("12_Risk_Score_vs_parameters.png")

    # Runs all EDA plots and stationarity tests, returns stationarity results
    def run_eda(self):
        print("\nRunning EDA ")
        steps = [
            self.plot_raw_series,
            self.plot_rolling_statistics,
            self.plot_decomposition,
            self.test_stationarity,
            self.plot_acf_pacf,
            self.plot_feature_correlations,
            self.plot_target_distribution,
            self.plot_calendar_heatmap,
            self.plot_yoy_comparison,
            self.plot_monthly_boxplots,
            self.plot_parameter_trends,
            self.plot_Risk_Score_vs_parameters,
        ]
        stationarity = {}
        for step in steps:
            try:
                result = step()
                if step.__name__ == "test_stationarity":
                    stationarity = result or {}
            except Exception as exc:
                print(f"  [WARN] {step.__name__} raised an unexpected error and was skipped: {exc}")
        print("EDA completed successfully.\n")
        return stationarity