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
from .citation_validation import validate_citations
from .release import (
    block_response,
    release_response,
    route_after_citation_validation,
)


def build_graph(synthesis_node=synthesize,
                checkpointer=None,
                interrupt_before=None,):
    builder = StateGraph(MedicalResearchState)

    builder.add_node("literature_research", literature_research)
    builder.add_node("internal_evidence", internal_evidence)
    builder.add_node("assess_evidence", assess_evidence)
    builder.add_node("synthesize", synthesis_node)
    builder.add_node("abstain", abstain)
    builder.add_node("validate_citations", validate_citations)
    builder.add_node("release_response", release_response)
    builder.add_node("block_response", block_response)

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

    builder.add_edge("synthesize", "validate_citations")
    builder.add_conditional_edges(
        "validate_citations",
        route_after_citation_validation,
        {
            "release": "release_response",
            "block": "block_response",
        },
    )
    builder.add_edge("release_response", END)
    builder.add_edge("block_response", END)

    return builder.compile(checkpointer=checkpointer, 
                           interrupt_before=interrupt_before,)