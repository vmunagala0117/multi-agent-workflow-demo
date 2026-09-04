from .state import MedicalResearchState


def literature_research(
    state: MedicalResearchState,
) -> dict:
    """Simulate retrieving evidence from external literature."""
    return {
        "literature_results": [
            {
                "source_id": "literature-001",
                "title": "Synthetic external research article",
                "summary": f"External evidence related to: {state['user_query']}",
            }
        ]
    }


def internal_evidence(
    state: MedicalResearchState,
) -> dict:
    """Simulate retrieving evidence from an internal knowledge base."""
    return {
        "internal_evidence": [
            {
                "source_id": "internal-001",
                "title": "Synthetic internal evidence document",
                "summary": f"Internal evidence related to: {state['user_query']}",
            }
        ]
    }


def synthesize(
    state: MedicalResearchState,
) -> dict:
    """Combine external and internal evidence into a placeholder response."""
    literature_count = len(state["literature_results"])
    internal_count = len(state["internal_evidence"])

    return {
        "synthesis": (
            f"Found {literature_count} external literature result(s) and "
            f"{internal_count} internal evidence result(s) for "
            f"'{state['user_query']}'."
        ),
        "citations": [
            *state["literature_results"],
            *state["internal_evidence"],
        ],
        "validation_status": "not_validated",
    }