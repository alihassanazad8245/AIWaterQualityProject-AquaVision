from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict

class ReportState(TypedDict, total=False):
    query: str                           # the user's natural-language request
    sample_data: Dict[str, Any]          # filled from the query (or supplied directly)
    template_type: str                   # 'sample', 'city', or 'trend'
    focus: Optional[str]                 # any special emphasis the user asked for
    not_provided: Optional[List[str]]    # parameters missing from the query
    error: Optional[str]
    selected_template_text: Optional[str]
    model_outputs: Optional[Dict[str, Any]]
    violations: Optional[List[Dict[str, Any]]]
    draft_narrative: Optional[str]
    recommendations: Optional[List[Dict[str, str]]]
    recommendations_text: Optional[str]
    narrative_source: Optional[str]
    narrative_warning: Optional[str]
    feature_engineering: Optional[List[Dict[str, str]]]
    parse_warning: Optional[str]
    numeric_qa_passed: Optional[bool]
    final_report_md: Optional[str]
    exported_file_path: Optional[str]
    exported_markdown_path: Optional[str]