from langgraph.graph import END, START, StateGraph

from .nodes import internal_evidence, literature_research, synthesize
from .state import MedicalResearchState


def build_graph():
    builder = StateGraph(MedicalResearchState)

    builder.add_node("literature_research", literature_research)
    builder.add_node("internal_evidence", internal_evidence)
    builder.add_node("synthesize", synthesize)

    builder.add_edge(START, "literature_research")
    builder.add_edge("literature_research", "internal_evidence")
    builder.add_edge("internal_evidence", "synthesize")
    builder.add_edge("synthesize", END)

    return builder.compile()