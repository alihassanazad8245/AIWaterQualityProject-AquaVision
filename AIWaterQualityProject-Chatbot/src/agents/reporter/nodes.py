import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Template

from src.agents.reporter.state import ReportState
from src.foundation.inference import model_runner
from src.foundation.rules import NSDWQ_LIMITS, TOXIC_PARAMS, rule_engine

ROOT_DIR = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = ROOT_DIR / "src" / "foundation" / "templates"

PARAMS = [
    "pH", "Turbidity", "TDS", "Chloride", "Sulfate", "Nitrate", "Fluoride",
    "Arsenic", "Iron", "Lead", "Cadmium", "Chromium", "Mercury",
]
ADDITIONAL_PARAMS = [
    "EC", "Hardness", "Calcium", "Magnesium", "Sodium", "Potassium",
    "Total Coliform", "E. Coli",
]
INPUT_PARAMS = PARAMS + ADDITIONAL_PARAMS
ALIASES = {
    "ph": "pH",
    "turbidity": "Turbidity",
    "tds": "TDS",
    "chloride": "Chloride",
    "sulfate": "Sulfate",
    "sulphate": "Sulfate",
    "nitrate": "Nitrate",
    "fluoride": "Fluoride",
    "arsenic": "Arsenic",
    "iron": "Iron",
    "lead": "Lead",
    "cadmium": "Cadmium",
    "chromium": "Chromium",
    "mercury": "Mercury",
    "electrical conductivity": "EC",
    "conductivity": "EC",
    "ec": "EC",
    "hardness": "Hardness",
    "calcium": "Calcium",
    "magnesium": "Magnesium",
    "sodium": "Sodium",
    "potassium": "Potassium",
    "total coliform": "Total Coliform",
    "coliform": "Total Coliform",
    "e. coli": "E. Coli",
    "e coli": "E. Coli",
    "escherichia coli": "E. Coli",
}
TREATMENT = {
    "Arsenic": "Use arsenic-specific removal (adsorptive media, coagulation-filtration) or reverse osmosis; switch to an alternate safe source meanwhile.",
    "Lead": "Replace lead-bearing plumbing; use certified lead-removal filters or reverse osmosis.",
    "Cadmium": "Use reverse osmosis or ion exchange and trace the industrial or agricultural source.",
    "Chromium": "Use ion exchange or reverse osmosis and investigate nearby industrial discharge.",
    "Mercury": "Use activated carbon or reverse osmosis and identify the contamination source.",
    "Nitrate": "Use ion exchange or reverse osmosis and review fertilizer or sewage influence on the source.",
    "Fluoride": "Use activated alumina or reverse osmosis defluoridation.",
    "TDS": "Use reverse osmosis or dilution with a lower-TDS source.",
    "Chloride": "Use reverse osmosis or blending and check for saline intrusion.",
    "Sulfate": "Use reverse osmosis or ion exchange.",
    "Iron": "Use aeration followed by sand filtration.",
    "Turbidity": "Use coagulation, sedimentation and sand filtration.",
    "pH": "Adjust pH using a treatment plan appropriate to the measured acidity or alkalinity.",
    "Microbial": "Disinfect with chlorination, UV or boiling; inspect the source for sewage contamination.",
}
UNITS = {
    **{name: limits["unit"] for name, limits in NSDWQ_LIMITS.items()},
    "EC": "µS/cm",
    "Hardness": "mg/L",
    "Calcium": "mg/L",
    "Magnesium": "mg/L",
    "Sodium": "mg/L",
    "Potassium": "mg/L",
    "Total Coliform": "CFU/100 mL",
    "E. Coli": "CFU/100 mL",
}
CLASS_SEVERITY = {
    "Excellent": 0,
    "Good": 1,
    "Poor": 2,
    "Very Poor": 3,
    "Unsuitable": 4,
    "Unsuitable for Drinking": 4,
}


def get_llm(temperature: float = 0.1):
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL") or "gemini-3.8-flash",
        temperature=temperature,
        google_api_key=api_key,
        thinking_level="low",
        max_tokens=2048,
        request_timeout=45,
        retries=2,
    )


def _text(res: Any) -> str:
    content = res.content
    if isinstance(content, str):
        return content
    return "".join(
        part.get("text", "") if isinstance(part, dict) else str(part)
        for part in content
    )


def _llm_parse(query: str) -> Dict[str, Any]:
    prompt = (
        "Extract only water-quality information explicitly stated by the user. "
        "Reply with ONLY a JSON object, no markdown, with these keys:\n"
        '  "parameters": object mapping parameter name to a number. Allowed names: '
        f"{INPUT_PARAMS}. Include only stated measurements.\n"
        '  "microbial_detected": true, false, or null if unknown\n'
        '  "city", "province", "resource_type", "sample_id", "sampling_date", '
        '"sampling_location", "collected_by", "laboratory", "report_no": '
        "strings or null\n"
        '  "actual_wqi": number or null if not stated\n'
        '  "template_type": "sample"\n'
        '  "focus": a short string or null\n\n'
        f"User request: {query}"
    )
    response = _text(get_llm(temperature=0).invoke(prompt))
    response = re.sub(r"^```(?:json)?|```$", "", response.strip(), flags=re.M).strip()
    parsed = json.loads(response)
    if not isinstance(parsed, dict):
        raise ValueError("The report parser did not return a JSON object.")
    return parsed


def _regex_parse(query: str) -> Dict[str, float]:
    found: Dict[str, float] = {}
    for alias, name in sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = rf"\b{re.escape(alias)}\b\s*(?:is|was|=|:|of|at)?\s*(-?\d+(?:\.\d+)?)"
        match = re.search(pattern, query, re.I)
        if match:
            found[name] = float(match.group(1))
    return found


def _metadata_from_query(query: str) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    fields = {
        "sample_id": r"(?:sample\s*(?:id|no\.?))",
        "sampling_date": r"(?:sampling\s*date|sample\s*date)",
        "sampling_location": r"(?:sampling\s*location|location|site)",
        "collected_by": r"(?:collected\s*by)",
        "laboratory": r"(?:laboratory|lab)",
        "report_no": r"(?:report\s*(?:no\.?|number))",
        "city": r"(?:city)",
        "province": r"(?:province)",
        "resource_type": r"(?:resource\s*type|water\s*source)",
    }
    for key, label in fields.items():
        match = re.search(
            rf"\b{label}\s*[:=]\s*(.+?)(?=\s*[,;]|\.\s|\s+\b(?:sample\s*(?:id|no\.?)|sampling\s*date|"
            r"sample\s*date|sampling\s*location|collected\s*by|laboratory|"
            r"lab|report\s*(?:no\.?|number)|city|province|resource\s*type|water\s*source)\b|$)",
            query,
            re.I,
        )
        if match:
            metadata[key] = match.group(1).strip().rstrip(".")
    actual_wqi = re.search(
        r"\bactual\s+wqi(?:\s+score)?\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        query,
        re.I,
    )
    if actual_wqi:
        metadata["actual_wqi"] = float(actual_wqi.group(1))
    return metadata


def _known_parameter_keys(sample: Dict[str, Any]) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for key, value in sample.items():
        normalized_key = re.sub(r"\s*\([^)]*\)\s*$", "", str(key).strip())
        canonical = ALIASES.get(
            normalized_key.lower(),
            ALIASES.get(str(key).strip().lower()),
        )
        if canonical and value is not None:
            values[canonical] = value
    return values


def query_parse_node(state: ReportState) -> ReportState:
    if state.get("sample_data"):
        state.setdefault("template_type", "sample")
        return state

    query = state.get("query", "")
    parsed: Dict[str, Any] = {}
    if (
        (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        and not _regex_parse(query)
    ):
        try:
            parsed = _llm_parse(query)
        except Exception as exc:
            state["parse_warning"] = (
                f"Gemini parsing failed ({type(exc).__name__}); "
                "using explicit-value parsing."
            )

    params: Dict[str, Any] = {}
    for key, value in (parsed.get("parameters") or {}).items():
        normalized_key = re.sub(r"\s*\([^)]*\)\s*$", "", str(key).strip())
        canonical = ALIASES.get(
            normalized_key.lower(),
            ALIASES.get(str(key).strip().lower()),
        )
        if canonical and isinstance(value, (int, float)):
            params[canonical] = float(value)
    params.update({key: value for key, value in _regex_parse(query).items() if key not in params})

    if not any(name in params for name in PARAMS):
        state["error"] = (
            "I couldn't find a water-quality measurement in your request. "
            "Include a reading such as 'pH 7.2, TDS 450 mg/L, Arsenic 0.01 mg/L'."
        )
        return state

    metadata = _metadata_from_query(query)
    for key in (
        "sample_id", "sampling_date", "sampling_location", "collected_by",
        "laboratory", "report_no", "city", "province", "resource_type",
        "actual_wqi",
    ):
        if parsed.get(key) is not None:
            metadata[key] = parsed[key]
    microbial = parsed.get("microbial_detected")
    if microbial is None:
        if re.search(r"\b(?:microbial|bacteria|coliform|e\.?\s*coli)\b.*\b(?:present|detected|positive)\b", query, re.I):
            microbial = True
        elif re.search(r"\b(?:microbial|bacteria|coliform|e\.?\s*coli)\b.*\b(?:absent|not detected|negative)\b", query, re.I):
            microbial = False
    if microbial is not None:
        params["Microbial_Status"] = int(bool(microbial))

    state["sample_data"] = {
        **params,
        "City": metadata.get("city") or "N/A",
        "Province": metadata.get("province") or "N/A",
        "Resource_Type": metadata.get("resource_type") or "N/A",
        "Sample_ID": metadata.get("sample_id") or "Not provided",
        "Sampling_Date": metadata.get("sampling_date") or "Not provided",
        "Sampling_Location": metadata.get("sampling_location") or "Not provided",
        "Collected_By": metadata.get("collected_by") or "Not provided",
        "Laboratory": metadata.get("laboratory") or "Not provided",
        "Report_No": metadata.get("report_no") or "Not provided",
        "Actual_WQI": metadata.get("actual_wqi"),
    }
    state["template_type"] = "sample"
    state["focus"] = parsed.get("focus")
    state["not_provided"] = [parameter for parameter in PARAMS if parameter not in params]
    return state


def _risk_assessment(violations: List[Dict[str, Any]]) -> tuple[int, str]:
    chemical_count = sum(
        1 for violation in violations
        if violation["parameter"] in TOXIC_PARAMS
    )
    microbial = any(
        violation["parameter"] == "Microbial" for violation in violations
    )
    tds_exceeded = any(
        violation["parameter"] == "TDS" for violation in violations
    )
    if chemical_count == 0 and not microbial:
        score = 2 if tds_exceeded else 0
    elif chemical_count == 0 and tds_exceeded and microbial:
        score = 4
    elif chemical_count == 0:
        score = 1
    elif chemical_count == 1 and microbial:
        score = 4
    elif chemical_count == 1:
        score = 3
    elif microbial:
        score = 6
    else:
        score = 5
    category = {
        0: "Marginally Safe",
        1: "Low",
        2: "Low",
        3: "Medium",
        4: "Medium-High",
        5: "High",
        6: "High",
    }[score]
    return score, category


def _models_disagree(predictions: Dict[str, Any]) -> bool:
    wqi_severity = CLASS_SEVERITY.get(predictions["wqi_category"], 0)
    class_severity = CLASS_SEVERITY.get(
        predictions["final_water_quality_class"], wqi_severity
    )
    return abs(wqi_severity - class_severity) >= 2


def data_fetch_node(state: ReportState) -> ReportState:
    sample = dict(state["sample_data"])
    sample.update(_known_parameter_keys(sample))
    if "Microbial_Status" not in sample:
        has_microbial_measurement = any(
            sample.get(parameter) is not None
            for parameter in ("Total Coliform", "E. Coli")
        )
        if has_microbial_measurement:
            sample["Microbial_Status"] = int(any(
                float(sample[parameter]) > 0
                for parameter in ("Total Coliform", "E. Coli")
                if sample.get(parameter) is not None
            ))
    predictions = model_runner.predict_sample(sample)
    forecast = model_runner.forecast_risk(steps=60, start_after=date.today())
    violations = rule_engine.evaluate_violations(sample)
    risk_score, risk_category = _risk_assessment(violations)
    predictions["risk_score"] = risk_score
    predictions["risk_category"] = risk_category

    annual_forecast = []
    previous = None
    for start in range(0, len(forecast), 12):
        year_values = forecast[start:start + 12]
        if len(year_values) != 12:
            break
        annual = year_values[-1]
        predicted = float(annual["predicted_risk_score"])
        trend = (
            "↑" if previous is not None and predicted > previous + 0.05
            else "↓" if previous is not None and predicted < previous - 0.05
            else "→"
        )
        annual_forecast.append({
            "year": start // 12 + 1,
            "period": f"{year_values[0]['period']} to {year_values[-1]['period']}",
            "predicted_risk_score": f"{predicted:.2f}",
            "confidence_interval": annual["confidence_interval"],
            "risk_category": annual["risk_category"],
            "trend": trend,
        })
        previous = predicted

    state["sample_data"] = sample
    state["model_outputs"] = {
        "predictions": predictions,
        "forecast": annual_forecast,
        "forecast_monthly": forecast,
    }
    state["violations"] = violations
    state["feature_engineering"] = predictions["feature_engineering"]
    return state


def template_selection_node(state: ReportState) -> ReportState:
    path = TEMPLATE_DIR / "sample_report.md"
    state["template_type"] = "sample"
    state["selected_template_text"] = path.read_text(encoding="utf-8")
    return state


def _recommendations(violations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    recommendations = []
    for violation in violations:
        parameter = violation["parameter"]
        text = TREATMENT.get(parameter)
        if text is None:
            continue
        urgent = violation["severity"] == "critical"
        recommendations.append({
            "text": text,
            "category": parameter,
            "priority": "High" if urgent else "Medium",
            "timeline": "Immediate" if urgent else "Short-term",
        })
    if not recommendations:
        recommendations.append({
            "text": "Continue routine monitoring and test any parameters not measured in this sample.",
            "category": "Monitoring",
            "priority": "Low",
            "timeline": "Long-term",
        })
    return recommendations


def narrative_drafting_node(state: ReportState) -> ReportState:
    predictions = state["model_outputs"]["predictions"]
    violations = state["violations"]
    sample = state["sample_data"]
    missing = state.get("not_provided") or []
    recommendations = _recommendations(violations)
    state["recommendations"] = recommendations
    recommendation_text = " ".join(
        item["text"] for item in recommendations
    )
    state["recommendations_text"] = recommendation_text

    has_api_key = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    if has_api_key:
        prompt = (
            "Write a concise technical narrative for a water-quality report. "
            "Use only these measurements and model results; do not invent facts.\n"
            f"Request: {state.get('query', '')}\n"
            f"Focus: {state.get('focus') or 'none'}\n"
            f"Measurements: {sample}\n"
            f"Model results: {predictions}\n"
            f"NSDWQ violations: {violations}\n"
            f"Parameters not supplied: {missing}\n"
            "Explain health implications only for detected violations and identify "
            "the result as a model estimate where appropriate."
        )
        try:
            state["draft_narrative"] = _text(get_llm().invoke(prompt))
            state["narrative_source"] = "Gemini"
            return state
        except Exception as exc:
            state["narrative_warning"] = (
                f"Gemini narrative generation failed ({type(exc).__name__}); "
                "using a local model-based summary."
            )

    result = (
        f"The CatBoost regression model estimates a WQI of "
        f"{predictions['wqi_calculated']} ({predictions['wqi_category']}). "
        f"The {predictions['classification_model']} classifier assigns "
        f"{predictions['final_water_quality_class']} with "
        f"{predictions['classification_confidence']:.1f}% confidence."
    )
    if violations:
        result += (
            " Reported measurements exceed these applicable limits: "
            + "; ".join(
                f"{v['parameter']} {v['value']} {v['unit']} "
                f"(limit {v['limit']})"
                for v in violations
            )
            + "."
        )
    else:
        result += (
            " No NSDWQ exceedances were identified among the parameters "
            "reported for this sample."
        )
    if _models_disagree(predictions):
        result += (
            " The regression WQI category and classifier water-quality "
            "class differ substantially; verify both against laboratory "
            "measurements."
        )
    if predictions["microbial_status"] == "Not reported":
        result += " Microbial test results were not provided."
    if missing:
        result += (
            " The measured-parameter interpretation is limited because "
            f"these WQI parameters were not supplied: {', '.join(missing)}."
        )
    result += (
        " The five-year risk forecast is a separate population time-series "
        "forecast and is not a sample-specific prediction."
    )
    state["draft_narrative"] = result
    state["narrative_source"] = (
        "Local model-based summary (Gemini request failed)"
        if has_api_key else
        "Local model-based summary (Gemini API key not configured)"
    )
    return state


def _format_metric(value: Any, digits: int = 4) -> str:
    if value is None:
        return "Not available"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def numeric_qa_node(state: ReportState) -> ReportState:
    sample = state["sample_data"]
    predictions = state["model_outputs"]["predictions"]
    violations = state["violations"]
    forecast_values = state["model_outputs"]["forecast"]
    metrics = predictions["regression_metrics"]
    forecast_metrics = predictions["forecast_metrics"]
    report_date = date.today().isoformat()
    actual_wqi = sample.get("Actual_WQI", sample.get("WQI"))
    if actual_wqi is None:
        actual_wqi_text = "Not provided"
        absolute_error = "Not available"
        actual_wqi_remark = "No laboratory WQI value supplied"
        absolute_error_remark = "Cannot calculate without an actual WQI"
    else:
        actual_wqi = float(actual_wqi)
        actual_wqi_text = f"{actual_wqi:.2f}"
        absolute_error = f"{abs(actual_wqi - predictions['wqi_calculated']):.2f}"
        actual_wqi_remark = "Supplied reference value"
        absolute_error_remark = "Absolute difference from supplied value"

    class_probabilities = predictions["class_probabilities"]
    recommendation_rows = state["recommendations"]
    resource_type = sample.get("Resource_Type", "N/A")
    final_class = predictions["final_water_quality_class"]
    risk_category = predictions["risk_category"]
    risk_score = predictions["risk_score"]
    model_disagreement = _models_disagree(predictions)
    forecast_trend = (
        "Increasing" if forecast_values and forecast_values[-1]["trend"] == "↑"
        else "Decreasing" if forecast_values and forecast_values[-1]["trend"] == "↓"
        else "Stable"
    )
    reported = [
        {
            "parameter": parameter,
            "unit": UNITS.get(parameter, ""),
            "value": sample[parameter],
            "limit": (
                f"{NSDWQ_LIMITS[parameter]['min']}–{NSDWQ_LIMITS[parameter]['max']}"
                if NSDWQ_LIMITS.get(parameter, {}).get("min") is not None
                else NSDWQ_LIMITS[parameter]["max"]
            ) if parameter in NSDWQ_LIMITS else (
                "0 (absence expected)" if parameter in ("Total Coliform", "E. Coli")
                else "Not specified"
            ),
            "remark": "Exceeds" if any(
                violation["parameter"] == parameter for violation in violations
            ) else "Within reported limit",
        }
        for parameter in INPUT_PARAMS
        if sample.get(parameter) is not None
    ]
    metric_lookup = {key.casefold(): value for key, value in metrics.items()}
    forecast_metric_lookup = {
        key.casefold(): value for key, value in forecast_metrics.items()
    }
    sample_id = sample.get("Sample_ID", "Not provided")
    report_no = sample.get("Report_No")
    if not report_no or report_no == "Not provided":
        report_no = f"WQI-{datetime.now():%Y%m%d-%H%M%S}"

    context = {
        "sample_id": sample_id,
        "sampling_date": sample.get("Sampling_Date", "Not provided"),
        "province": sample.get("Province", "N/A"),
        "city": sample.get("City", "N/A"),
        "resource_type": resource_type,
        "sampling_location": sample.get("Sampling_Location", "Not provided"),
        "collected_by": sample.get("Collected_By", "Not provided"),
        "report_date": report_date,
        "laboratory": sample.get("Laboratory", "Not provided"),
        "report_no": report_no,
        "input_features": reported,
        "feature_engineering": state["feature_engineering"],
        "wqi_category_model": "CatBoost regression + WQI thresholds",
        "wqi_category": predictions["wqi_category"],
        "wqi_category_confidence": "N/A (threshold-derived)",
        "wqi_category_actual": "Not provided",
        "final_class_model": predictions["classification_model"],
        "final_class": final_class,
        "final_class_confidence": f"{predictions['classification_confidence']:.1f}%",
        "final_class_actual": "Not provided",
        "microbial_model": "Laboratory measurement / NSDWQ rule",
        "microbial": predictions["microbial_status"],
        "microbial_confidence": "Not applicable",
        "microbial_actual": (
            predictions["microbial_status"]
            if predictions["microbial_status"] != "Not reported"
            else "Not provided"
        ),
        "risk_category_model": "NSDWQ violation risk rules",
        "risk_category": risk_category,
        "risk_category_confidence": "Rule-derived",
        "risk_category_actual": "Not provided",
        "class_probabilities": class_probabilities,
        "regression_model": predictions["regression_model"],
        "regression_model_remark": "Selected trained WQI regression model",
        "actual_wqi": actual_wqi_text,
        "actual_wqi_remark": actual_wqi_remark,
        "wqi_score": f"{predictions['wqi_calculated']:.2f}",
        "predicted_wqi_remark": "CatBoost single-sample estimate",
        "absolute_error": absolute_error,
        "absolute_error_remark": absolute_error_remark,
        "wqi_category_remark": "Based on the predicted WQI score",
        "r2_score": _format_metric(metric_lookup.get("r2_score")),
        "rmse": _format_metric(metric_lookup.get("rmse")),
        "mae": _format_metric(metric_lookup.get("mae")),
        "mape": "Not reported in saved regression evaluation",
        "forecast_values": forecast_values,
        "forecast_model": predictions["forecast_model"],
        "training_period": predictions["forecast_training_period"],
        "forecast_metric": (
            f"RMSE={_format_metric(forecast_metric_lookup.get('rmse'))}; "
            f"MAE={_format_metric(forecast_metric_lookup.get('mae'))}; "
            f"MAPE={_format_metric(forecast_metric_lookup.get('mape'), 2)}%"
        ),
        "wqi_interpretation": (
            f"{predictions['wqi_category']} category from predicted WQI "
            f"{predictions['wqi_calculated']:.2f}"
        ),
        "final_class_interpretation": (
            f"Classifier output: {final_class} "
            f"({predictions['classification_confidence']:.1f}% confidence); "
            "confirm with laboratory results."
        ),
        "microbial_interpretation": (
            "Microbial contamination was reported."
            if predictions["microbial_status"] == "Contaminated"
            else "No microbial contamination was reported."
            if predictions["microbial_status"] == "Not detected"
            else "No microbial test result was supplied."
        ),
        "risk_interpretation": (
            f"{risk_category} rule-derived risk (score {risk_score}/6) "
            "from reported NSDWQ exceedances."
        ),
        "risk_trend": forecast_trend,
        "risk_trend_interpretation": (
            f"ARIMA population risk forecast trend over the five-year horizon: "
            f"{forecast_trend.lower()}."
        ),
        "narrative": state["draft_narrative"],
        "conclusion": (
            f"The models estimate WQI {predictions['wqi_calculated']:.2f} "
            f"({predictions['wqi_category']}) and classify the sample as "
            f"{final_class} with {predictions['classification_confidence']:.1f}% "
            "confidence. These are screening estimates, not a substitute for "
            "a certified laboratory assessment."
        ),
        "key_concerns": "; ".join(
            [
                *(
                    f"{v['parameter']} ({v['severity']} exceedance)"
                    for v in violations
                ),
                *(
                    ["Regression and classification outputs differ substantially; "
                     "confirm the sample with laboratory results."]
                    if model_disagreement else []
                ),
                *(
                    ["No exceedances detected in the parameters reported; "
                     "unmeasured parameters were not assessed."]
                    if not violations else []
                ),
            ]
        ),
        "recommendations": recommendation_rows,
        "prepared_by": "Water Quality Analysis System",
        "reviewed_by": "Not assigned",
        "approved_by": "Not assigned",
        "violations": violations,
        "narrative_source": state.get("narrative_source", ""),
        "recommendations_text": state["recommendations_text"],
    }
    markdown = Template(state["selected_template_text"]).render(**context)
    if state.get("not_provided"):
        markdown += (
            "\n\n### Data completeness\n"
            "No measurement was supplied for these WQI parameters: "
            + ", ".join(state["not_provided"])
            + ". Model features not supplied were imputed using training-data "
            "medians; see Table 2."
        )
    required_numbers = [
        f"{predictions['wqi_calculated']:.2f}",
        f"{predictions['classification_confidence']:.1f}%",
    ]
    state["numeric_qa_passed"] = all(
        number in markdown for number in required_numbers
    ) and all(
        item["predicted_risk_score"] in markdown for item in forecast_values
    )
    if not state["numeric_qa_passed"]:
        raise ValueError(
            "Report quality check failed: one or more model results are absent "
            "from the rendered report."
        )
    state["final_report_md"] = markdown
    return state
