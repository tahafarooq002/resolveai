from langgraph.graph import StateGraph, END

from app.ai.state import TicketState
from app.ai.nodes import triage_agent, resolution_agent, quality_agent


def build_support_graph():
    """
    Multi-agent style workflow:
    Triage Agent → Resolution Agent → Quality Assurance Agent → END
    (Retrieval is injected before the graph runs)
    """
    workflow = StateGraph(TicketState)

    workflow.add_node("triage", triage_agent)
    workflow.add_node("resolution", resolution_agent)
    workflow.add_node("quality", quality_agent)

    workflow.set_entry_point("triage")
    workflow.add_edge("triage", "resolution")
    workflow.add_edge("resolution", "quality")
    workflow.add_edge("quality", END)

    return workflow.compile()


support_graph = build_support_graph()
