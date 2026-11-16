"""Chatbot link to the project dataset (Classification/WQIResults/wqi_full_dataset.csv).

The first two columns of the CSV (``Sampling Date`` and ``Province``) are ignored on load, so the
chatbot only ever sees City, Resource Type, the measured parameters, the WQI columns, the microbial
columns, the risk columns and the composite ``Water_Quality_Class``.

The dataset is queried deterministically with pandas (no LLM-written code): for a data question the
store detects which cities / resource types / classes / parameters the question mentions, filters the
rows, computes the requested statistics, and returns a compact text block that the chatbot's
generation step uses as grounded context.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "Classification" / "WQIResults" / "wqi_full_dataset.csv"
SKIP_LEADING_COLUMNS = 2  # Sampling Date, Province

CITY_COL = "City"
RESOURCE_COL = "Resource Type"
CLASS_COL = "Water_Quality_Class"          # composite class (worst-penalty-wins)
WQI_CAT_COL = "WQI_Category"
MICROBIAL_COL = "Microbial_Status"
RISK_CAT_COL = "Risk_Category"

# Strong signals: the user is clearly asking about the dataset itself.
_STRONG_TRIGGER = re.compile(
    r"\b(dataset|data set|records?|rows?|columns?|how many|number of|average|median|"
    r"percent(?:age)?|proportion|distribution|statistics|stats|summary of|summari[sz]e)\b", re.I)
# Weak signals also occur in general questions ("maximum permissible limit", "what does TDS mean"),
# so they only count when the question also names the data (cities / resource types / samples).
_WEAK_TRIGGER = re.compile(
    r"\b(count|mean|maximum|minimum|max|min|highest|lowest|worst|best|top|share|compare|comparison|"
    r"profile|exceed\w*|violat\w*|rank\w*|most|least|cleanest|which cit(?:y|ies)|which resource)\b", re.I)
_DATA_NOUNS = re.compile(r"\b(cit(?:y|ies)|resource types?|samples?|sources?)\b", re.I)
_STAT_WORDS = re.compile(r"\b(average|mean|median|summary|summari[sz]e|statistics|stats|profile|"
                         r"max|maximum|min|minimum|highest|lowest)\b", re.I)
_EXCEED_WORDS = re.compile(r"\b(exceed\w*|violat\w*|above the limit|over the limit|beyond|"
                           r"within (?:the )?limits?|compl\w+ with)\b", re.I)
_RANK_WORDS = re.compile(r"\b(highest|lowest|worst|best|top|most|least|rank\w*|cleanest)\b", re.I)
_ASC_WORDS = re.compile(r"\b(lowest|best|least|cleanest|min(?:imum)?)\b", re.I)
_IGNORED_COLUMN_WORDS = re.compile(
    r"\b(province\w*|punjab|sindh|balochistan|khyber|kpk|gilgit|baltistan|ajk|azad|"
    r"year|years|date|dates|month|monthly|trend)\b", re.I)

# aliases -> lower-case parameter key (the column name without its unit)
_PARAM_ALIASES = {
    "total dissolved solids": "tds",
    "electrical conductivity": "ec",
    "conductivity": "ec",
    "sulphate": "sulfate",
    "coliform": "total coliform",
    "coliforms": "total coliform",
    "e coli": "e. coli",
    "ecoli": "e. coli",
    "escherichia coli": "e. coli",
    "temp": "temperature",
    "water quality index": "wqi",
}

# Pakistan NSDWQ maximum limits already used by the project's rule engine (src/foundation/rules.py)
_LIMIT_KEYS = {
    "turbidity": "Turbidity", "tds": "TDS", "chloride": "Chloride", "sulfate": "Sulfate",
    "nitrate": "Nitrate", "fluoride": "Fluoride", "arsenic": "Arsenic", "iron": "Iron",
}


def _fmt(x) -> str:
    if pd.isna(x):
        return "n/a"
    x = float(x)
    if x != 0 and (abs(x) >= 1e5 or abs(x) < 1e-3):
        return f"{x:.3g}"
    return f"{x:,.4g}" if abs(x) < 1000 else f"{x:,.1f}"


def _base_name(column: str) -> str:
    return re.sub(r"\s*\(.*?\)", "", column).strip().lower()


class DatasetStore:
    def __init__(self, path: Path = DATASET_PATH, skip_leading: int = SKIP_LEADING_COLUMNS):
        raw = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                raw = pd.read_csv(path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if raw is None:
            raise ValueError(f"Could not read {path}")
        self.path = path
        self.ignored_columns: List[str] = list(raw.columns[:skip_leading])
        self.df: pd.DataFrame = raw.iloc[:, skip_leading:].copy()
        self.columns: List[str] = list(self.df.columns)

        cat_cols = [CITY_COL, RESOURCE_COL, CLASS_COL, WQI_CAT_COL, MICROBIAL_COL, RISK_CAT_COL,
                    "Water Quality Class"]
        self.numeric_cols = [c for c in self.columns
                             if c not in cat_cols and pd.api.types.is_numeric_dtype(self.df[c])]
        # parameter key -> list of columns ("wqi" is ambiguous: project-computed first)
        self.param_cols: Dict[str, List[str]] = {}
        for col in self.numeric_cols:
            self.param_cols.setdefault(_base_name(col), []).append(col)
        self.param_cols["wqi"] = [c for c in ("WQI_Calculated", "WQI") if c in self.numeric_cols]
        # chemical / physical parameters (everything that is a measurement, not a derived score)
        derived = {"WQI", "WQI_Calculated", "Risk_Score"}
        self.measurement_cols = [c for c in self.numeric_cols if c not in derived]

    # ------------------------------------------------------------------ detection
    def is_data_query(self, query: str) -> bool:
        q = query or ""
        if _STRONG_TRIGGER.search(q):
            return True
        if _WEAK_TRIGGER.search(q):
            return bool(_DATA_NOUNS.search(q) or self._match_values(q.lower(), CITY_COL)
                        or self._match_values(q.lower(), RESOURCE_COL))
        return False

    def _find_parameters(self, q: str) -> List[Tuple[str, List[str]]]:
        """Parameter keys mentioned in the question (longest alias first, no overlapping matches)."""
        keys = {k: k for k in self.param_cols}
        keys.update({a: t for a, t in _PARAM_ALIASES.items() if t in self.param_cols})
        found: List[Tuple[str, List[str]]] = []
        masked = q.lower()
        for alias in sorted(keys, key=len, reverse=True):
            pat = rf"(?<![a-z_]){re.escape(alias)}(?![a-z_])"
            if re.search(pat, masked):
                masked = re.sub(pat, " " * len(alias), masked)
                target = keys[alias]
                if all(target != f[0] for f in found):
                    found.append((target, self.param_cols[target]))
        return found

    def _value_pattern(self, value: str) -> str:
        v = value.lower().replace(" for drinking", "")
        parts = [re.escape(p) for p in v.split()]
        return r"(?<![a-z])" + r"\s*".join(parts) + r"s?(?![a-z])"

    def _match_values(self, q: str, column: str, gate: bool = True) -> List[str]:
        if column not in self.df.columns or not gate:
            return []
        values = sorted(self.df[column].dropna().unique(), key=len, reverse=True)
        hits, masked = [], q.lower()
        for v in values:
            pat = self._value_pattern(str(v))
            if re.search(pat, masked):
                masked = re.sub(pat, " ", masked)
                hits.append(v)
        return hits

    # ------------------------------------------------------------------ context builder
    def build_context(self, query: str) -> Optional[str]:
        if not self.is_data_query(query):
            return None
        q = query.lower()

        # ---- filters
        cities = self._match_values(q, CITY_COL)
        resources = self._match_values(q, RESOURCE_COL)
        class_col = WQI_CAT_COL if re.search(r"wqi[ _]category", q) else CLASS_COL
        class_gate = bool(re.search(r"class|categor|classified|rated|water quality|wqi|unsuitable|"
                                    r"excellent|very poor", q))
        classes = self._match_values(q, class_col, gate=class_gate)
        micro = []
        if re.search(r"contaminated|unsafe", q):
            micro = ["Contaminated"]
        elif re.search(r"microbial(?:ly)?\s+safe|bacteriologically safe", q):
            micro = ["Safe"]
        risks = self._match_values(q, RISK_CAT_COL, gate="risk" in q)

        df = self.df
        applied = []
        for col, vals in ((CITY_COL, cities), (RESOURCE_COL, resources), (class_col, classes),
                          (MICROBIAL_COL, micro), (RISK_CAT_COL, risks)):
            if vals:
                df = df[df[col].isin(vals)]
                applied.append(f"{col} in {vals}")

        params = self._find_parameters(q)
        param_columns = [c for _, cols in params for c in cols]

        lines: List[str] = []
        lines.append(f"Source: {self.path.name} ({len(self.df)} samples; "
                     f"Sampling Date and Province are not available to the chatbot).")
        if re.search(r"column|field|dataset|data set|summar|available|what data", q):
            lines.append("Columns available: " + ", ".join(self.columns))
        if _IGNORED_COLUMN_WORDS.search(q):
            lines.append("NOTE: the question refers to province / date / year information, which is "
                         "NOT available in this dataset view. Say that it cannot be answered by "
                         "province or date; any figures below cover ALL cities, not a province.")
        lines.append("Filters applied: " + ("; ".join(applied) if applied else "none (all samples)")
                     + f" -> {len(df)} matching samples.")

        if df.empty:
            lines.append("No samples match these filters.")
            return "\n".join(lines)

        # ---- distributions
        def dist(col: str, label: str):
            counts = df[col].value_counts(dropna=True)
            total = counts.sum()
            if total:
                lines.append(f"{label}: " + ", ".join(
                    f"{k} {v} ({v / total * 100:.1f}%)" for k, v in counts.items()))

        dist(class_col, f"{class_col} distribution")
        dist(MICROBIAL_COL, "Microbial_Status")
        dist(RISK_CAT_COL, "Risk_Category")
        if class_col != WQI_CAT_COL:
            dist(WQI_CAT_COL, "WQI_Category")

        # ---- parameter statistics
        stat_cols = list(dict.fromkeys(param_columns))
        if not stat_cols and _STAT_WORDS.search(q):
            stat_cols = list(self.numeric_cols)
        if stat_cols:
            lines.append("Parameter statistics (non-missing values only; n = values present):")
            for col in stat_cols:
                s = df[col].dropna()
                if s.empty:
                    lines.append(f"- {col}: no values in this subset")
                    continue
                lines.append(f"- {col}: n={len(s)}, mean={_fmt(s.mean())}, median={_fmt(s.median())}, "
                             f"min={_fmt(s.min())}, max={_fmt(s.max())}")

        # ---- parameters asked about but not present in the CSV
        for name in ("lead", "cadmium", "chromium", "mercury"):
            if re.search(rf"\b{name}\b", q):
                lines.append(f"NOTE: {name.capitalize()} is not a column in this dataset.")

        # ---- exceedance of NSDWQ limits (limits from src/foundation/rules.py)
        if _EXCEED_WORDS.search(q):
            lines.extend(self._exceedance_lines(df, params))

        # ---- ranking of cities / resource types
        if _RANK_WORDS.search(q):
            lines.extend(self._ranking_lines(df, q, params))

        text = "\n".join(lines)
        return text if len(text) <= 6000 else text[:6000] + "\n...(truncated)"

    def _exceedance_lines(self, df: pd.DataFrame, params) -> List[str]:
        from src.foundation.rules import NSDWQ_LIMITS
        keys = [k for k, _ in params] or list(_LIMIT_KEYS) + ["ph"]
        out = ["Exceedance of Pakistan NSDWQ limits (limits from the project rule engine):"]
        any_line = False
        for key in keys:
            if key == "ph" and "pH" in df.columns:
                s = df["pH"].dropna()
                lim = NSDWQ_LIMITS["pH"]
                bad = int(((s < lim["min"]) | (s > lim["max"])).sum())
                out.append(f"- pH outside {lim['min']}-{lim['max']}: {bad} of {len(s)} samples "
                           f"({bad / max(len(s), 1) * 100:.1f}%)")
                any_line = True
            elif key in _LIMIT_KEYS:
                name = _LIMIT_KEYS[key]
                col = self.param_cols[key][0]
                s = df[col].dropna()
                limit = NSDWQ_LIMITS[name]["max"]
                bad = int((s > limit).sum())
                out.append(f"- {col} > {limit}: {bad} of {len(s)} samples "
                           f"({bad / max(len(s), 1) * 100:.1f}%)")
                any_line = True
        if "total coliform" in keys or "e. coli" in keys or not params:
            if MICROBIAL_COL in df.columns:
                bad = int((df[MICROBIAL_COL] == "Contaminated").sum())
                out.append(f"- Microbial contamination (E. coli or Total Coliform > 0): {bad} of "
                           f"{len(df)} samples ({bad / max(len(df), 1) * 100:.1f}%)")
                any_line = True
        return out if any_line else ["No NSDWQ limit is defined in the project rules for the "
                                     "parameters mentioned."]

    def _ranking_lines(self, df: pd.DataFrame, q: str, params) -> List[str]:
        group_col = RESOURCE_COL if re.search(r"resource|source type|type of water|water type", q) else CITY_COL
        metric = (params[0][1][0] if params else "WQI_Calculated")
        ascending = bool(_ASC_WORDS.search(q))
        g = df.groupby(group_col)[metric].agg(["mean", "count"]).dropna()
        if g.empty:
            return []
        solid = g[g["count"] >= 3]
        note = ""
        if len(solid) >= 3:
            g, note = solid, " (groups with fewer than 3 samples excluded)"
        g = g.sort_values("mean", ascending=ascending).head(5)
        order = "lowest" if ascending else "highest"
        out = [f"Top {len(g)} {group_col} values by {order} mean {metric}{note}:"]
        out += [f"- {idx}: mean={_fmt(r['mean'])} (n={int(r['count'])})" for idx, r in g.iterrows()]
        return out


@lru_cache(maxsize=1)
def get_dataset_store() -> DatasetStore:
    return DatasetStore()