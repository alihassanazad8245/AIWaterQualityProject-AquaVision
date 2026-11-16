"""Pakistan NSDWQ threshold checks."""

"""Pakistan NSDWQ threshold checks."""
from typing import Any, Dict, List

# (min, max) -> None means no bound. Values in mg/L unless noted.
# Double-check these against your Pakistan_NSDWQ_Standards CSV and edit as needed.
NSDWQ_LIMITS: Dict[str, Dict[str, Any]] = {
    "pH":        {"min": 6.5, "max": 8.5,   "unit": ""},
    "Turbidity": {"min": None, "max": 5.0,  "unit": "NTU"},
    "TDS":       {"min": None, "max": 1000.0, "unit": "mg/L"},
    "Chloride":  {"min": None, "max": 250.0, "unit": "mg/L"},
    "Sulfate":   {"min": None, "max": 250.0, "unit": "mg/L"},
    "Nitrate":   {"min": None, "max": 50.0,  "unit": "mg/L"},
    "Fluoride":  {"min": None, "max": 1.5,   "unit": "mg/L"},
    "Arsenic":   {"min": None, "max": 0.05,  "unit": "mg/L"},
    "Iron":      {"min": None, "max": 0.3,   "unit": "mg/L"},
    "Lead":      {"min": None, "max": 0.05,  "unit": "mg/L"},
    "Cadmium":   {"min": None, "max": 0.01,  "unit": "mg/L"},
    "Chromium":  {"min": None, "max": 0.05,  "unit": "mg/L"},
    "Mercury":   {"min": None, "max": 0.001, "unit": "mg/L"},
}

TOXIC_PARAMS = {"Arsenic", "Lead", "Cadmium", "Chromium", "Mercury", "Nitrate", "Fluoride"}


class RuleEngine:
    def evaluate_violations(self, sample: Dict[str, Any]) -> List[Dict[str, Any]]:
        violations: List[Dict[str, Any]] = []
        for param, lim in NSDWQ_LIMITS.items():
            if param not in sample or sample[param] is None:
                continue
            val = float(sample[param])
            if lim["max"] is not None and val > lim["max"]:
                violations.append({
                    "parameter": param, "value": val, "limit": lim["max"],
                    "unit": lim["unit"], "type": "above_max",
                    "severity": "critical" if param in TOXIC_PARAMS else "moderate",
                })
            elif lim["min"] is not None and val < lim["min"]:
                violations.append({
                    "parameter": param, "value": val, "limit": lim["min"],
                    "unit": lim["unit"], "type": "below_min", "severity": "moderate",
                })
        if int(sample.get("Microbial_Status", 0)) == 1:
            violations.append({
                "parameter": "Microbial", "value": 1, "limit": 0, "unit": "",
                "type": "contaminated", "severity": "critical",
            })
        return violations


rule_engine = RuleEngine()