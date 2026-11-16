"""Load the trained water-quality models and prepare single-sample predictions."""

import warnings
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]

CLASSIFICATION_FEATURES = [
    "Total Coliform",
    "Arsenic (mg/L)",
    "TDS (mg/L)",
    "Potassium (mg/L)",
    "Sodium (mg/L)",
    "Magnesium (mg/L)",
    "Nitrate (mg/L)",
    "Turbidity (NTU)",
    "Calcium (mg/L)",
    "Chloride (mg/L)",
    "EC (µS/cm)",
    "Hardness (mg/L)",
]

FEATURE_TO_PARAMETER = {
    "pH": "pH",
    "Turbidity (NTU)": "Turbidity",
    "TDS (mg/L)": "TDS",
    "Chloride (mg/L)": "Chloride",
    "Sulfate (mg/L)": "Sulfate",
    "Nitrate (mg/L)": "Nitrate",
    "Fluoride (mg/L)": "Fluoride",
    "Arsenic (mg/L)": "Arsenic",
    "Iron (mg/L)": "Iron",
    "Lead (mg/L)": "Lead",
    "Cadmium (mg/L)": "Cadmium",
    "Chromium (mg/L)": "Chromium",
    "Mercury (mg/L)": "Mercury",
    "Total Coliform": "Total Coliform",
    "E. Coli": "E. Coli",
    "EC (µS/cm)": "EC",
    "Hardness (mg/L)": "Hardness",
    "Calcium (mg/L)": "Calcium",
    "Magnesium (mg/L)": "Magnesium",
    "Sodium (mg/L)": "Sodium",
    "Potassium (mg/L)": "Potassium",
}

CLASSIFICATION_LABELS = [
    "Excellent",
    "Good",
    "Poor",
    "Unsuitable",
    "Very Poor",
]
QUERY_PARAMETER_ALIASES = {
    "electrical conductivity": "EC",
    "total coliform": "Total Coliform",
    "escherichia coli": "E. Coli",
    "chloride": "Chloride",
    "sulfate": "Sulfate",
    "sulphate": "Sulfate",
    "nitrate": "Nitrate",
    "fluoride": "Fluoride",
    "arsenic": "Arsenic",
    "hardness": "Hardness",
    "calcium": "Calcium",
    "magnesium": "Magnesium",
    "sodium": "Sodium",
    "potassium": "Potassium",
    "turbidity": "Turbidity",
    "mercury": "Mercury",
    "chromium": "Chromium",
    "cadmium": "Cadmium",
    "coliform": "Total Coliform",
    "lead": "Lead",
    "iron": "Iron",
    "conductivity": "EC",
    "ec": "EC",
    "e. coli": "E. Coli",
    "e coli": "E. Coli",
    "ph": "pH",
    "tds": "TDS",
}


def _as_float(value: Any) -> float:
    """Convert a sample measurement to a finite float."""
    number = float(value)
    if not pd.notna(number):
        raise ValueError(f"Expected a finite numeric sample value, got {value!r}.")
    return number


def parse_sample_query(query: str) -> Dict[str, Any]:
    """Extract numeric measurements from a chatbot request without inventing data."""
    sample: Dict[str, Any] = {}
    for alias, name in sorted(
        QUERY_PARAMETER_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        match = re.search(
            rf"\b{re.escape(alias)}\b\s*(?:is|was|=|:|of|at)?\s*(-?\d+(?:\.\d+)?)",
            query,
            re.I,
        )
        if match:
            sample[name] = float(match.group(1))
    detected = bool(re.search(
        r"\b(?:microbial|bacteria|coliform|e\.?\s*coli)\b.*"
        r"\b(?:present|detected|positive)\b",
        query,
        re.I,
    ))
    not_detected = bool(re.search(
        r"\b(?:microbial|bacteria|coliform|e\.?\s*coli)\b.*"
        r"\b(?:absent|not detected|negative)\b",
        query,
        re.I,
    ))
    if detected or not_detected:
        sample["Microbial_Status"] = int(detected)
    return sample


def _model_feature_value(sample: Dict[str, Any], feature: str) -> Any:
    parameter = FEATURE_TO_PARAMETER.get(feature, feature)
    if parameter in sample and sample[parameter] is not None:
        return sample[parameter]
    if feature in sample and sample[feature] is not None:
        return sample[feature]
    if feature == "Total Coliform":
        ecoli = sample.get("E. Coli")
        if ecoli is not None:
            return max(_as_float(ecoli), 0.0)
        if sample.get("Microbial_Status") is not None:
            return int(bool(sample["Microbial_Status"]))
    return None


def _classification_statistics(
    feature_names: List[str],
) -> Dict[str, Dict[str, float]]:
    data_path = ROOT_DIR / "Classification" / "data" / "wq_pakistan.xlsx"
    raw = pd.read_excel(data_path, sheet_name="merged_file.csv")
    statistics: Dict[str, Dict[str, float]] = {}

    for feature in feature_names:
        source_column = (
            feature if feature in raw.columns
            else FEATURE_TO_PARAMETER.get(feature, feature)
        )
        if source_column not in raw.columns:
            raise ValueError(
                f"Training data for classifier feature {feature!r} "
                f"was not found in {data_path}."
            )
        values = raw[source_column].replace(
            {"BDL": 0, "bdl": 0, "Bdl": 0}
        )
        numeric = pd.to_numeric(values, errors="coerce")
        median = float(numeric.median())
        numeric = numeric.fillna(median)
        q1, q3 = numeric.quantile([0.25, 0.75])
        spread = float(q3 - q1)
        lower = float(q1 - 1.5 * spread)
        upper = float(q3 + 1.5 * spread)
        capped = numeric.clip(lower=lower, upper=upper)
        scale = float(capped.std(ddof=0))
        statistics[feature] = {
            "median": median,
            "lower": lower,
            "upper": upper,
            "mean": float(capped.mean()),
            "scale": scale if scale else 1.0,
        }
    return statistics


def _regression_training_frame() -> pd.DataFrame:
    path = ROOT_DIR / "Regression" / "Datapreparation" / "df_model_ready.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"Regression training features are missing: {path}"
        )
    return pd.read_csv(path)


def _model_metrics(path: Path, model_name: str) -> Dict[str, float]:
    if not path.is_file():
        return {}
    metrics = pd.read_csv(path)
    name_column = next(
        (column for column in ("Model", "model") if column in metrics.columns),
        None,
    )
    if name_column is None:
        return {}
    matching = metrics.loc[
        metrics[name_column].astype(str).str.casefold()
        == model_name.casefold()
    ]
    if matching.empty:
        return {}
    return {
        str(column): float(value)
        for column, value in matching.iloc[0].items()
        if column != name_column and pd.notna(value)
    }


class ModelRunner:
    """Run the saved classifier, WQI regressor, and risk forecaster."""

    def __init__(self) -> None:
        self._classification_model: Any = None
        self._classification_model_name = ""
        self._classification_labels: List[str] = []
        self._classification_stats: Dict[str, Dict[str, float]] = {}
        self._regression_model: Any = None
        self._regression_features: List[str] = []
        self._regression_frame: pd.DataFrame | None = None
        self._regression_categories: pd.DataFrame | None = None
        self._forecast_model: Any = None
        self._forecast_training_period = "Training dates unavailable"
        self._last_feature_engineering: List[Dict[str, str]] = []

    def _load_classification_model(self) -> None:
        if self._classification_model is not None:
            return

        model_dir = ROOT_DIR / "Classification" / "Models"
        candidates = (
            ("final_model.pkl", "Tuned Gradient Boosting"),
            ("random_forest.pkl", "Random Forest"),
            ("decision_tree.pkl", "Decision Tree"),
        )
        load_errors = []
        for filename, name in candidates:
            path = model_dir / filename
            if not path.is_file():
                load_errors.append(f"{filename}: file not found")
                continue
            try:
                self._classification_model = joblib.load(path)
            except (ImportError, AttributeError, ValueError) as exc:
                load_errors.append(f"{filename}: {exc}")
                warnings.warn(
                    f"Could not load classifier {path}: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                continue
            self._classification_model_name = name
            break
        if self._classification_model is None:
            details = "; ".join(load_errors)
            raise RuntimeError(
                f"No compatible classification model could be loaded: {details}"
            )

        feature_names = list(
            getattr(
                self._classification_model,
                "feature_names_in_",
                CLASSIFICATION_FEATURES,
            )
        )
        if len(feature_names) != int(self._classification_model.n_features_in_):
            raise ValueError(
                "The classification model feature list does not match "
                "the model's trained input width."
            )
        self._classification_stats = _classification_statistics(feature_names)

        labels_path = (
            ROOT_DIR / "Classification" / "TransformedData"
            / "transformed_data.csv"
        )
        if labels_path.is_file():
            labels = pd.read_csv(
                labels_path, usecols=["Water_Quality_Class"]
            )["Water_Quality_Class"]
            self._classification_labels = sorted(
                str(value) for value in labels.dropna().unique()
            )
        else:
            self._classification_labels = CLASSIFICATION_LABELS.copy()
        if not self._classification_labels:
            raise ValueError(
                f"No class labels were found in {labels_path}."
            )

    def _load_regression_model(self) -> None:
        if self._regression_model is not None:
            return
        path = ROOT_DIR / "Regression" / "Models" / "catboost_initial.pkl"
        if not path.is_file():
            raise FileNotFoundError(f"Trained WQI regression model is missing: {path}")
        self._regression_model = joblib.load(path)
        model_features = list(getattr(self._regression_model, "feature_names_", []))
        if model_features and all(model_features):
            self._regression_features = model_features
        else:
            selected_path = (
                ROOT_DIR / "Regression" / "FeatureSelection"
                / "mostcorrelatedfeatures.csv"
            )
            selected = pd.read_csv(selected_path)
            feature_column = "Most Correlated Features"
            if feature_column not in selected.columns:
                raise ValueError(
                    f"Selected regression features are missing from {selected_path}."
                )
            self._regression_features = selected[feature_column].dropna().tolist()
        self._regression_frame = _regression_training_frame()
        category_path = (
            ROOT_DIR / "Regression" / "Datapreparation" / "df_cleaned.csv"
        )
        if category_path.is_file():
            self._regression_categories = pd.read_csv(category_path)
        expected_count = int(getattr(self._regression_model, "n_features_in_", 0))
        if expected_count <= 0:
            expected_count = len(
                getattr(self._regression_model, "feature_names_", self._regression_features)
            )
        if len(self._regression_features) != expected_count:
            raise ValueError(
                "The regression feature list does not match the trained "
                "CatBoost model input width."
            )

    def _load_forecast_model(self) -> None:
        if self._forecast_model is not None:
            return
        path = ROOT_DIR / "Forecasting" / "Models" / "arima_model.pkl"
        if not path.is_file():
            raise FileNotFoundError(f"Trained risk forecast model is missing: {path}")
        model = joblib.load(path)
        history_path = (
            ROOT_DIR / "Forecasting" / "DataIngestion" / "ts_resampled.csv"
        )
        if history_path.is_file():
            history = pd.read_csv(
                history_path,
                usecols=["Date", "Risk_Score"],
                parse_dates=["Date"],
            ).set_index("Date")["Risk_Score"]
            if history.index.has_duplicates or not history.index.is_monotonic_increasing:
                raise ValueError(
                    f"Forecast training dates in {history_path} must be unique "
                    "and increasing."
                )
            if history.isna().any():
                raise ValueError(
                    f"Risk_Score values in {history_path} contain missing data."
                )
            model_labels = getattr(model.model.data, "row_labels", None)
            if model_labels is not None and len(model_labels):
                model_start = pd.Timestamp(model_labels[0])
                model_end = pd.Timestamp(model_labels[-1])
                if model_start not in history.index or model_end not in history.index:
                    raise ValueError(
                        "The saved ARIMA model dates do not overlap the current "
                        "historical risk-score series."
                    )
                training_history = history.loc[model_start:model_end]
                if len(training_history) != int(model.nobs):
                    raise ValueError(
                        "The saved ARIMA model's training dates do not align "
                        "with the current historical risk-score series."
                    )
                newer_observations = history.loc[history.index > model_end]
                if not newer_observations.empty:
                    model = model.append(newer_observations, refit=True)
        self._forecast_model = model
        labels = getattr(self._forecast_model.model.data, "row_labels", None)
        if labels is not None and len(labels):
            first_date = pd.Timestamp(labels[0])
            last_date = pd.Timestamp(labels[-1])
        else:
            history = pd.read_csv(
                history_path, usecols=["Date"], parse_dates=["Date"]
            )
            training_rows = min(int(self._forecast_model.nobs), len(history))
            first_date = pd.Timestamp(history.iloc[0]["Date"])
            last_date = pd.Timestamp(history.iloc[training_rows - 1]["Date"])
        self._forecast_training_period = (
            f"{first_date:%Y-%m} to {last_date:%Y-%m} "
            f"({int(self._forecast_model.nobs)} monthly observations)"
        )

    @staticmethod
    def _standardize(value: float, mean: float, scale: float) -> float:
        return (value - mean) / (scale if scale else 1.0)

    def _classification_input(
        self, sample: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
        self._load_classification_model()
        feature_names = list(self._classification_model.feature_names_in_)
        row: Dict[str, float] = {}
        engineering = []
        for feature in feature_names:
            value = _model_feature_value(sample, feature)
            stats = self._classification_stats[feature]
            input_text = "Not provided"
            if value is None:
                numeric = stats["median"]
                method = "Training median imputation + IQR capping + StandardScaler"
            else:
                numeric = _as_float(value)
                input_text = str(value)
                method = "IQR capping + StandardScaler"
            capped = min(max(numeric, stats["lower"]), stats["upper"])
            engineered = self._standardize(
                capped, stats["mean"], stats["scale"]
            )
            row[feature] = engineered
            engineering.append({
                "feature": f"Classification: {feature}",
                "method": method,
                "input_value": input_text,
                "engineered_value": f"{engineered:.4f}",
            })
        return pd.DataFrame([row], columns=feature_names), engineering

    def _regression_input(
        self, sample: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
        self._load_regression_model()
        assert self._regression_frame is not None
        row: Dict[str, float] = {}
        engineering = []
        resource_type = str(sample.get("Resource_Type", "")).strip().casefold()
        for feature in self._regression_features:
            if feature.startswith("Resource Type_"):
                category = feature.removeprefix("Resource Type_").casefold()
                value = float(resource_type == category)
                input_text = str(sample.get("Resource_Type") or "Not provided")
                method = "One-hot encoding + StandardScaler"
                if (
                    self._regression_categories is not None
                    and "Resource Type" in self._regression_categories.columns
                ):
                    category_values = (
                        self._regression_categories["Resource Type"]
                        .fillna("")
                        .astype(str)
                        .str.casefold()
                    )
                    mean = float((category_values == category).mean())
                    scale = (mean * (1.0 - mean)) ** 0.5 or 1.0
                elif feature in self._regression_frame.columns:
                    mean = float(self._regression_frame[feature].mean())
                    scale = float(
                        self._regression_frame[feature].std(ddof=0)
                    ) or 1.0
                else:
                    raise ValueError(
                        f"Cannot reconstruct training statistics for "
                        f"regression feature {feature!r}."
                    )
            else:
                value = _model_feature_value(sample, feature)
                input_text = "Not provided" if value is None else str(value)
                method = "Training median imputation + StandardScaler"
                if value is None:
                    value = float(self._regression_frame[feature].median())
                else:
                    method = "StandardScaler"
                    value = _as_float(value)
                mean = float(self._regression_frame[feature].mean())
                scale = float(self._regression_frame[feature].std(ddof=0)) or 1.0
            engineered = self._standardize(float(value), mean, scale)
            row[feature] = engineered
            engineering.append({
                "feature": f"Regression: {feature}",
                "method": method,
                "input_value": input_text,
                "engineered_value": f"{engineered:.4f}",
            })
        return pd.DataFrame([row], columns=self._regression_features), engineering

    def predict_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        if not sample:
            raise ValueError("A water-quality sample is required for prediction.")

        classification_input, classification_features = self._classification_input(
            sample
        )
        regression_input, regression_features = self._regression_input(sample)

        class_index = int(self._classification_model.predict(classification_input)[0])
        class_probabilities = self._classification_model.predict_proba(
            classification_input
        )[0]
        class_name = (
            self._classification_labels[class_index]
            if 0 <= class_index < len(self._classification_labels)
            else str(class_index)
        )
        class_order = getattr(
            self._classification_model, "classes_", range(len(class_probabilities))
        )
        probability_rows = []
        for encoded_class, probability in zip(class_order, class_probabilities):
            label_index = int(encoded_class)
            label = (
                self._classification_labels[label_index]
                if 0 <= label_index < len(self._classification_labels)
                else str(encoded_class)
            )
            probability_rows.append({
                "class_name": label,
                "probability": f"{float(probability) * 100:.1f}%",
                "_value": float(probability),
            })
        probability_rows.sort(key=lambda item: item["_value"], reverse=True)
        for rank, item in enumerate(probability_rows, start=1):
            item["rank"] = rank
            item.pop("_value")

        predicted_wqi = max(
            0.0, float(self._regression_model.predict(regression_input)[0])
        )
        self._load_forecast_model()
        self._last_feature_engineering = (
            classification_features + regression_features
        )

        microbial_known = (
            sample.get("Microbial_Status") is not None
            or sample.get("Total Coliform") is not None
            or sample.get("E. Coli") is not None
        )
        microbial_detected = bool(sample.get("Microbial_Status", 0)) or any(
            _as_float(sample[key]) > 0
            for key in ("Total Coliform", "E. Coli")
            if sample.get(key) is not None
        )
        microbial_status = (
            "Contaminated" if microbial_detected
            else "Not detected" if microbial_known
            else "Not reported"
        )

        metrics_root = ROOT_DIR / "Regression" / "ModelComparison"
        regression_metrics = _model_metrics(
            metrics_root / "final_model_comparison.csv", "CatBoost"
        )
        forecast_metrics = _model_metrics(
            ROOT_DIR / "Forecasting" / "ModelComparison"
            / "final_comparison.csv",
            "ARIMA",
        )
        return {
            "wqi_calculated": round(predicted_wqi, 2),
            "wqi_category": _wqi_category(predicted_wqi),
            "final_water_quality_class": class_name,
            "microbial_status": microbial_status,
            "classification_model": self._classification_model_name,
            "classification_confidence": round(
                max(float(value) for value in class_probabilities) * 100, 1
            ),
            "class_probabilities": probability_rows,
            "regression_model": "CatBoost",
            "regression_metrics": regression_metrics,
            "forecast_model": "ARIMA",
            "forecast_metrics": forecast_metrics,
            "forecast_training_period": self._forecast_training_period,
            "feature_engineering": self._last_feature_engineering,
        }

    def forecast_risk(
        self, steps: int = 7, start_after: Any = None
    ) -> List[Dict[str, Any]]:
        if steps < 1:
            raise ValueError("Forecast steps must be a positive integer.")
        self._load_forecast_model()
        row_labels = getattr(self._forecast_model.model.data, "row_labels", None)
        if row_labels is not None and len(row_labels):
            last_date = pd.Timestamp(row_labels[-1])
        else:
            history_path = (
                ROOT_DIR / "Forecasting" / "DataIngestion" / "ts_resampled.csv"
            )
            history = pd.read_csv(history_path, usecols=["Date"], parse_dates=["Date"])
            last_date = pd.Timestamp(history.iloc[int(self._forecast_model.nobs) - 1]["Date"])

        skipped_steps = 0
        if start_after is not None:
            next_requested_month = pd.Timestamp(start_after).to_period("M") + 1
            first_forecast_month = last_date.to_period("M") + 1
            skipped_steps = max(
                0,
                next_requested_month.ordinal - first_forecast_month.ordinal,
            )
        total_steps = skipped_steps + steps
        forecast = self._forecast_model.get_forecast(
            steps=total_steps
        ).summary_frame()
        future_dates = pd.date_range(
            start=last_date + pd.offsets.MonthEnd(1),
            periods=total_steps,
            freq="ME",
        )

        rows = []
        previous = float(self._forecast_model.model.endog.squeeze()[-1])
        for index, (_, result) in enumerate(forecast.iterrows()):
            score = min(6.0, max(0.0, float(result["mean"])))
            lower = min(6.0, max(0.0, float(result["mean_ci_lower"])))
            upper = min(6.0, max(0.0, float(result["mean_ci_upper"])))
            if score > previous + 0.05:
                trend = "↑"
            elif score < previous - 0.05:
                trend = "↓"
            else:
                trend = "→"
            if index < skipped_steps:
                previous = score
                continue
            relative_index = index - skipped_steps
            rows.append({
                "day": relative_index + 1,
                "year": future_dates[index].year,
                "period": future_dates[index].strftime("%Y-%m"),
                "predicted_wqi": score,
                "predicted_risk_score": round(score, 2),
                "confidence_interval": f"{lower:.2f}–{upper:.2f}",
                "lower_confidence": lower,
                "upper_confidence": upper,
                "risk_category": _risk_category(score),
                "trend": trend,
            })
            previous = score
        return rows


def _wqi_category(wqi: float) -> str:
    if wqi <= 50:
        return "Excellent"
    if wqi <= 100:
        return "Good"
    if wqi <= 200:
        return "Poor"
    if wqi <= 300:
        return "Very Poor"
    return "Unsuitable for drinking"


def _risk_category(score: float) -> str:
    if score < 1:
        return "Marginally Safe"
    if score < 3:
        return "Low"
    if score < 5:
        return "Medium"
    return "High"


model_runner = ModelRunner()
