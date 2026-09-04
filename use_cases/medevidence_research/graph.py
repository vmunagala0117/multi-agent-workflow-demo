from langgraph.graph import END, START, StateGraph

from .nodes import (
    abstain,
    assess_evidence,
    internal_evidence,
    literature_research,
    route_after_assessment,
    synthesize,
)
from .state import MedicalResearchState


def build_graph():
    builder = StateGraph(MedicalResearchState)

    builder.add_node("literature_research", literature_research)
    builder.add_node("internal_evidence", internal_evidence)
    builder.add_node("assess_evidence", assess_evidence)
    builder.add_node("synthesize", synthesize)
    builder.add_node("abstain", abstain)

    builder.add_edge(START, "literature_research")
    builder.add_edge(START, "internal_evidence")

    builder.add_edge(
        ["literature_research", "internal_evidence"],
        "assess_evidence",
    )

    builder.add_conditional_edges(
        "assess_evidence",
        route_after_assessment,
        {
            "synthesize": "synthesize",
            "abstain": "abstain",
        },
    )

    builder.add_edge("synthesize", END)
    builder.add_edge("abstain", END)

    return builder.compile()