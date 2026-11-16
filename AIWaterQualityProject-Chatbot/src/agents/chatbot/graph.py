from langgraph.graph import StateGraph, END
from src.agents.chatbot.state import ChatbotState
from src.agents.chatbot.nodes import (
    router_node,
    tool_call_node,
    retrieval_node,
    dataset_node,
    generation_node,
    self_check_node,
    report_question_node,
)

class ChatbotGraphBuilder:
    """Build the chatbot workflow while keeping its LangGraph nodes callable."""

    @staticmethod
    def route_decision(state: ChatbotState) -> str:
        """Returns the exact name of the destination node."""
        if state.get("report_context"):
            return "report_question_node"
        route = state.get("route", "rag")
        if route == "tool" or route == "hybrid":
            return "tool_node"
        return "retrieval_node"

    def build(self):
        workflow = StateGraph(ChatbotState)

        workflow.add_node("router", router_node)
        workflow.add_node("tool_node", tool_call_node)
        workflow.add_node("retrieval_node", retrieval_node)
        workflow.add_node("dataset_node", dataset_node)
        workflow.add_node("generation", generation_node)
        workflow.add_node("self_check", self_check_node)
        workflow.add_node("report_question_node", report_question_node)

        workflow.set_entry_point("router")
        workflow.add_conditional_edges(
            "router",
            route_decision,
            {
                "tool_node": "tool_node",
                "retrieval_node": "retrieval_node",
                "report_question_node": "report_question_node",
            }
        )

        workflow.add_edge("report_question_node", END)
        workflow.add_edge("tool_node", "retrieval_node")
        workflow.add_edge("retrieval_node", "dataset_node")
        workflow.add_edge("dataset_node", "generation")
        workflow.add_edge("generation", "self_check")
        workflow.add_edge("self_check", END)

        return workflow.compile()


_graph_builder = ChatbotGraphBuilder()


def route_decision(state: ChatbotState) -> str:
    return _graph_builder.route_decision(state)


def build_chatbot_graph():
    return _graph_builder.build()

# Export chatbot_agent instance
chatbot_agent = build_chatbot_graph()