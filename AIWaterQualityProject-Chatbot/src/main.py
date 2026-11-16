import sys
from pathlib import Path
from datetime import date
import math
import re
from typing import Any
from dotenv import load_dotenv

# 1. Force stdout to flush immediately
sys.stdout.reconfigure(line_buffering=True)

# 2. Add project root to sys.path so 'src' imports work from anywhere
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 3. Load .env file explicitly from the project root
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

print(">>> Starting Execution...")
print(f">>> Project Root: {ROOT_DIR}")

# 4. Import the agents after paths and env are initialized
try:
    from src.agents.chatbot.graph import chatbot_agent
    from src.agents.reporter.graph import report_agent
    from src.agents.reporter.nodes import INPUT_PARAMS, UNITS
    from src.foundation.vector_store import ingest_standards
    from src.foundation.pdf_rag import ingest_methodology
    print(">>> All agent modules imported successfully.")
except Exception as e:
    print(f"[Import Error]: {e}")
    sys.exit(1)


DEFAULT_CHAT_QUERY = (
    "What are the health risks of drinking groundwater with high nitrate levels for children?"
)
DEFAULT_REPORT_QUERY = (
    f"Generate a sample report. Sample ID: DEMO-001, "
    f"sampling date: {date.today().isoformat()}, "
    "sampling location: Demo site, collected by: Demo, laboratory: Demo lab, "
    "city: Lahore, province: Punjab, resource type: Groundwater. "
    "Measurements: pH 7.4, Turbidity 2.1, TDS 450, Chloride 110, Sulfate 90, "
    "Nitrate 12, Fluoride 0.8, Arsenic 0.01, Iron 0.1, Lead 0.005, "
    "Cadmium 0.001, Chromium 0.01, Mercury 0.0005, Total Coliform 0, "
    "E. coli 0, EC 500, Hardness 150, Calcium 40, Magnesium 30, "
    "Sodium 100, Potassium 10."
)


_REPORT_REQUEST = re.compile(
    r"\b(?:generate|create|make|prepare)\b.{0,80}\b(?:report|analysis)\b"
    r"|\b(?:run|start|perform|execute)\b.{0,80}\b(?:pipeline|analysis|test|report)\b"
    r"|\b(?:analy[sz]e|test|check|evaluate|assess)\b.{0,80}"
    r"\b(?:sample|readings?|measurements?|iot|water\s+data|results)\b",
    re.I,
)


def is_report_request(query: str) -> bool:
    return bool(_REPORT_REQUEST.search(query))


def _prompt_text(label: str) -> str:
    return input(f"{label} (press Enter to skip): ").strip()


def _prompt_measurement(parameter: str) -> float | None:
    unit = UNITS.get(parameter, "")
    suffix = f" ({unit})" if unit else ""
    while True:
        raw = input(f"{parameter}{suffix} (blank to skip): ").strip()
        if not raw:
            return None
        try:
            value = float(raw)
        except ValueError:
            print("Enter a numeric value, or leave it blank to skip.")
            continue
        if not math.isfinite(value):
            print("Enter a finite numeric value.")
            continue
        return value


def collect_sample_form() -> dict[str, Any]:
    print("\n--- Water sample form ---")
    print("Enter IoT/laboratory readings. Leave unknown fields blank.")
    sample = {
        "Sample_ID": _prompt_text("Sample ID") or "Not provided",
        "Sampling_Date": _prompt_text("Sampling date") or "Not provided",
        "Sampling_Location": _prompt_text("Sampling location") or "Not provided",
        "Collected_By": _prompt_text("Collected by") or "Not provided",
        "Laboratory": _prompt_text("Laboratory") or "Not provided",
        "Report_No": _prompt_text("Report number"),
        "City": _prompt_text("City") or "N/A",
        "Province": _prompt_text("Province") or "N/A",
        "Resource_Type": _prompt_text("Water source/resource type") or "N/A",
    }

    for parameter in INPUT_PARAMS:
        value = _prompt_measurement(parameter)
        if value is not None:
            sample[parameter] = value

    actual_wqi = _prompt_measurement("Actual WQI (optional reference)")
    if actual_wqi is not None:
        sample["Actual_WQI"] = actual_wqi

    if not any(sample.get(parameter) is not None for parameter in INPUT_PARAMS):
        raise ValueError("At least one water-quality measurement is required.")
    return sample


def _generate_report(query: str) -> str | None:
    try:
        sample = collect_sample_form()
    except ValueError as exc:
        print(f"\n[Cannot generate report]: {exc}")
        return None

    try:
        result = report_agent.invoke({
            "query": query,
            "sample_data": sample,
            "not_provided": [
                parameter for parameter in INPUT_PARAMS
                if sample.get(parameter) is None
            ],
        })
        if result.get("error"):
            print(f"\n[Cannot generate report]: {result['error']}")
            return None
        report = result.get("final_report_md")
        if not report:
            raise RuntimeError("The report pipeline returned no report content.")
        print("\n[Report generated]")
        print(f"[Word report]: {result.get('exported_file_path')}")
        print(f"[Markdown report]: {result.get('exported_markdown_path')}")
        if result.get("parse_warning"):
            print(f"[Report parsing notice]: {result['parse_warning']}")
        if result.get("narrative_warning"):
            print(f"[Report narrative notice]: {result['narrative_warning']}")
        print("You can now ask questions about this report.")
        return report
    except Exception as e:
        print(f"[Report generation error]: {e}")
        return None


def _answer_chat(query: str, report_context: str | None) -> None:
    print("\n[Working...]")
    try:
        output = chatbot_agent.invoke({
            "query": query,
            "report_context": report_context,
        })
        final_response = output.get("final_response") or "No response returned."
        warning = output.get("response_warning")
        if warning and warning not in final_response:
            print(f"\n[Chatbot notice]: {warning}")
        print("\n[Final Answer]:\n", final_response)
    except Exception as e:
        print(f"[Chatbot Execution Error]: {e}")


def run_chat_demo(query: str | None = None, interactive: bool = True):
    print("\n--- Water Quality Chatbot ---")
    print("Type 'exit' or 'quit' to end the chat.")
    report_context = None
    next_query = query
    while True:
        if next_query is None:
            if not interactive:
                return
            next_query = input("\nYou: ").strip()
        current_query = next_query
        next_query = None
        if not current_query:
            continue
        if current_query.casefold() in {"exit", "quit"}:
            return
        if is_report_request(current_query):
            generated_report = _generate_report(current_query)
            if generated_report is not None:
                report_context = generated_report
            continue
        _answer_chat(current_query, report_context)


def run_report_demo(query: str = DEFAULT_REPORT_QUERY):
    print("\n--- Running Agent 2 (Report Generator) ---")
    print(f"User Query: {query}")
    try:
        result = report_agent.invoke({"query": query})
        if result.get("error"):
            print(f"\n[Cannot generate report]: {result['error']}")
        else:
            print(f"\n[Report Generated Successfully]: {result.get('exported_file_path')}")
            print(f"[Markdown Report]: {result.get('exported_markdown_path')}")
        if result.get("parse_warning"):
            print(f"[Report Parsing Warning]: {result['parse_warning']}")
        if result.get("narrative_warning"):
            print(f"[Report Narrative Notice]: {result['narrative_warning']}")
    except Exception as e:
        print(f"[Report Execution Error]: {e}")


class WaterQualityApplication:
    """Dispatch the existing chat, report, and ingestion workflows."""

    def run(self, args: list[str]) -> None:
        if args and args[0] == "--ingest":
            print(">>> Running Vector Store Ingestion...")
            ingest_standards()
        elif args and args[0] == "--ingest-pdf":
            print(">>> Chunking + embedding the Methodology PDF (rules and Table 1) into ChromaDB...")
            ingest_methodology()
        elif args and args[0] == "--ingest-all":
            print(">>> Running Vector Store Ingestion (WHO/NSDWQ standards + Methodology PDF)...")
            ingest_standards()
            ingest_methodology()
        elif args and args[0] == "--report":
            run_report_demo(" ".join(args[1:]) or DEFAULT_REPORT_QUERY)
        elif args and args[0] == "--chat":
            run_chat_demo(" ".join(args[1:]) or None)
        elif args and args[0] == "--all":
            run_chat_demo(" ".join(args[1:]) or DEFAULT_CHAT_QUERY, interactive=False)
            run_report_demo(DEFAULT_REPORT_QUERY)
        else:
            query = input(
                "Enter a single-sample report request "
                "(press Enter to use the clearly marked demo sample): "
            ).strip() or DEFAULT_REPORT_QUERY
            run_report_demo(query)


if __name__ == "__main__":
    WaterQualityApplication().run(sys.argv[1:])