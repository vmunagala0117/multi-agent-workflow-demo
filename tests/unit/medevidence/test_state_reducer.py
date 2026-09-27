from langgraph.graph import END, START, StateGraph

from use_cases.medevidence_research.state import MedicalResearchState


def literature_failure(state: MedicalResearchState) -> dict:
    return {
        "errors": [
            {
                "node": "literature_research",
                "code": "TIMEOUT",
                "message": "Literature service timed out.",
                "retryable": True,
            }
        ]
    }


def internal_failure(state: MedicalResearchState) -> dict:
    return {
        "errors": [
            {
                "node": "internal_evidence",
                "code": "ACCESS_DENIED",
                "message": "Internal evidence access was denied.",
                "retryable": False,
            }
        ]
    }


def collect_results(state: MedicalResearchState) -> dict:
    return {}


def test_parallel_errors_are_aggregated() -> None:
    builder = StateGraph(MedicalResearchState)

    builder.add_node("literature_failure", literature_failure)
    builder.add_node("internal_failure", internal_failure)
    builder.add_node("collect_results", collect_results)

    builder.add_edge(START, "literature_failure")
    builder.add_edge(START, "internal_failure")

    builder.add_edge(
        ["literature_failure", "internal_failure"],
        "collect_results",
    )

    builder.add_edge("collect_results", END)

    graph = builder.compile()

    initial_state = {
        "user_query": "Test concurrent error aggregation",
        "literature_results": [],
        "internal_evidence": [],
        "synthesis": None,
        "citations": [],
        "validation_status": None,
        "errors": [],
    }

    final_state = graph.invoke(initial_state)

    assert len(final_state["errors"]) == 2
    assert {error["node"] for error in final_state["errors"]} == {
        "literature_research",
        "internal_evidence",
    }