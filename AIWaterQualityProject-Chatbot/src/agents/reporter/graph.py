import re
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, END
from src.agents.reporter.state import ReportState
from src.agents.reporter.nodes import (
    query_parse_node,
    data_fetch_node,
    template_selection_node,
    narrative_drafting_node,
    numeric_qa_node,
)
from src.agents.reporter.exporter import export_to_docx


class ReporterGraphBuilder:
    """Build the report workflow and handle its final file-export node."""

    @staticmethod
    def export_node(state: ReportState) -> ReportState:
        city = re.sub(
            r"[^A-Za-z0-9]+", "_", state["sample_data"].get("City", "report")
        ).strip("_")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(__file__).resolve().parents[3] / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        filename = f"Water_Quality_Report_{city or 'report'}_{stamp}"
        markdown_file = report_dir / f"{filename}.md"
        out_file = report_dir / f"{filename}.docx"
        content = state.get("final_report_md", "# Water Quality Report\nNo data generated.")
        markdown_file.write_text(content, encoding="utf-8")
        export_to_docx(content, str(out_file))
        state["exported_file_path"] = str(out_file)
        state["exported_markdown_path"] = str(markdown_file)
        return state

    @staticmethod
    def after_parse(state: ReportState) -> str:
        return "stop" if state.get("error") else "data_fetch"

    def build(self):
        workflow = StateGraph(ReportState)

        workflow.add_node("query_parse", query_parse_node)
        workflow.add_node("data_fetch", data_fetch_node)
        workflow.add_node("template_select", template_selection_node)
        workflow.add_node("narrative_draft", narrative_drafting_node)
        workflow.add_node("qa_check", numeric_qa_node)
        workflow.add_node("export", export_node)

        workflow.set_entry_point("query_parse")
        workflow.add_conditional_edges(
            "query_parse", after_parse, {"data_fetch": "data_fetch", "stop": END}
        )
        workflow.add_edge("data_fetch", "template_select")
        workflow.add_edge("template_select", "narrative_draft")
        workflow.add_edge("narrative_draft", "qa_check")
        workflow.add_edge("qa_check", "export")
        workflow.add_edge("export", END)

        return workflow.compile()


_graph_builder = ReporterGraphBuilder()


def export_node(state: ReportState) -> ReportState:
    return _graph_builder.export_node(state)


def after_parse(state: ReportState) -> str:
    return _graph_builder.after_parse(state)


def build_reporter_graph():
    return _graph_builder.build()


report_agent = build_reporter_graph()