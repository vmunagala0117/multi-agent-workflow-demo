from langgraph.graph import END, START, StateGraph

from .nodes import internal_evidence, literature_research, synthesize
from .state import MedicalResearchState


def build_graph():
    builder = StateGraph(MedicalResearchState)

    builder.add_node("literature_research", literature_research)
    builder.add_node("internal_evidence", internal_evidence)
    builder.add_node("synthesize", synthesize)

    # Fan-out: both evidence branches receive the initial state.
    builder.add_edge(START, "literature_research")
    builder.add_edge(START, "internal_evidence")

    # Fan-in barrier: synthesis waits for both branches.
    builder.add_edge(
        ["literature_research", "internal_evidence"],
        "synthesize",
    )

    builder.add_edge("synthesize", END)

    return builder.compile()