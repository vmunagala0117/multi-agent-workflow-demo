import pytest

from use_cases.medevidence_research.nodes import (
    assess_evidence,
    route_after_assessment,
)
from use_cases.medevidence_research.state import MedicalResearchState


def make_state(
    *,
    risk_level: str,
    has_literature: bool,
    has_internal: bool,
) -> MedicalResearchState:
    return {
        "user_query": "Test medical-evidence question",
        "risk_level": risk_level,
        "literature_results": (
            [{"source_id": "literature-001"}]
            if has_literature
            else []
        ),
        "internal_evidence": (
            [{"source_id": "internal-001"}]
            if has_internal
            else []
        ),
        "evidence_status": None,
        "response_mode": None,
        "synthesis": None,
        "citations": [],
        "validation_status": None,
        "errors": [],
    }


@pytest.mark.parametrize(
    (
        "risk_level",
        "has_literature",
        "has_internal",
        "expected_status",
        "expected_mode",
        "expected_route",
    ),
    [
        (
            "low",
            True,
            True,
            "complete",
            "full",
            "synthesize",
        ),
        (
            "low",
            True,
            False,
            "partial",
            "partial",
            "synthesize",
        ),
        (
            "high",
            True,
            False,
            "partial",
            "abstain",
            "abstain",
        ),
        (
            "low",
            False,
            False,
            "none",
            "abstain",
            "abstain",
        ),
    ],
)
def test_risk_based_evidence_routing(
    risk_level,
    has_literature,
    has_internal,
    expected_status,
    expected_mode,
    expected_route,
) -> None:
    state = make_state(
        risk_level=risk_level,
        has_literature=has_literature,
        has_internal=has_internal,
    )

    assessment = assess_evidence(state)
    updated_state = {**state, **assessment}

    assert assessment["evidence_status"] == expected_status
    assert assessment["response_mode"] == expected_mode
    assert route_after_assessment(updated_state) == expected_route