from typing import Optional, Dict, Any
from typing_extensions import TypedDict

class ChatbotState(TypedDict, total=False):
    query: str
    route: Optional[str]                # 'tool', 'rag', 'hybrid', or 'report'
    tool_output: Optional[Dict[str, Any]]
    retrieved_docs: Optional[str]
    draft_response: Optional[str]
    verification_passed: Optional[bool]
    final_response: Optional[str]
    methodology_docs: Optional[str]     # RAG chunks from the Methodology PDF (rules + Table 1)
    dataset_context: Optional[str]      # facts computed from wqi_full_dataset.csv
    report_context: Optional[str]
    response_warning: Optional[str]