import use_cases.medevidence_research.nodes as nodes
from use_cases.medevidence_research.state import (
    MedicalResearchState,
)


QUERY = (
    "What evidence supports Therapy Alpha for reducing chronic "
    "pruritus in adults, and what safety limitations remain?"
)


def make_state() -> MedicalResearchState:
    return {
        "user_query": QUERY,
        "risk_level": "low",
        "literature_results": [],
        "internal_evidence": [],
        "evidence_status": None,
        "response_mode": None,
        "synthesis": None,
        "citations": [],
        "validation_status": None,
        "errors": [],
    }


def test_literature_node_uses_retrieval_tool() -> None:
    update = nodes.literature_research(make_state())

    assert update["literature_results"]
    assert update["literature_results"][0]["source_id"] == "LIT-001"
    assert "errors" not in update


def test_internal_node_excludes_restricted_evidence() -> None:
    update = nodes.internal_evidence(make_state())

    result_ids = {
        result["source_id"]
        for result in update["internal_evidence"]
    }

    assert result_ids == {"INT-001", "INT-002"}
    assert "INT-003" not in result_ids
    assert "errors" not in update


def test_literature_failure_becomes_workflow_error(
    monkeypatch,
) -> None:
    def unavailable_tool(*args, **kwargs):
        raise OSError("Synthetic source failure")

    monkeypatch.setattr(
        nodes,
        "search_literature",
        unavailable_tool,
    )

    update = nodes.literature_research(make_state())

    assert update["literature_results"] == []
    assert update["errors"][0]["node"] == "literature_research"
    assert update["errors"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert update["errors"][0]["retryable"] is True