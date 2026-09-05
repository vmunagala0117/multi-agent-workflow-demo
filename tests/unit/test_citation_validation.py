from use_cases.medevidence_research.citation_validation import (
    validate_citations,
)
from use_cases.medevidence_research.schemas import (
    CitedFinding,
    EvidenceSynthesis,
)


def build_synthesis(
    efficacy_labels: list[str],
    safety_labels: list[str],
) -> EvidenceSynthesis:
    return EvidenceSynthesis(
        executive_summary="Synthetic evidence summary.",
        efficacy_findings=[
            CitedFinding(
                finding="Therapy Alpha improved the measured outcome.",
                citation_labels=efficacy_labels,
            )
        ],
        safety_findings=[
            CitedFinding(
                finding="Long-term safety evidence remains limited.",
                citation_labels=safety_labels,
            )
        ],
        evidence_gaps=["Evidence beyond one year is limited."],
        limitations=["The demonstration corpus is synthetic."],
    )


def build_state(synthesis_result: EvidenceSynthesis | None) -> dict:
    return {
        "literature_results": [
            {
                "citation_label": "[LIT-001]",
                "content": "Synthetic literature evidence.",
            }
        ],
        "internal_evidence": [
            {
                "citation_label": "[INT-001]",
                "content": "Synthetic internal evidence.",
            }
        ],
        "synthesis_result": synthesis_result,
        "errors": [],
    }


def test_known_citation_labels_are_valid() -> None:
    state = build_state(
        build_synthesis(
            efficacy_labels=["[LIT-001]"],
            safety_labels=["[INT-001]"],
        )
    )

    update = validate_citations(state)

    assert update == {"validation_status": "valid"}


def test_unknown_citation_label_is_invalid() -> None:
    state = build_state(
        build_synthesis(
            efficacy_labels=["[LIT-001]", "[MADE-UP-001]"],
            safety_labels=["[INT-001]"],
        )
    )

    update = validate_citations(state)

    assert update["validation_status"] == "invalid"
    assert update["errors"][0]["node"] == "validate_citations"
    assert update["errors"][0]["code"] == "UNKNOWN_CITATION_LABEL"
    assert "[MADE-UP-001]" in update["errors"][0]["message"]


def test_missing_synthesis_result_is_invalid() -> None:
    state = build_state(synthesis_result=None)

    update = validate_citations(state)

    assert update["validation_status"] == "invalid"
    assert update["errors"][0]["node"] == "validate_citations"
    assert update["errors"][0]["code"] == "MISSING_SYNTHESIS_RESULT"
    assert update["errors"][0]["retryable"] is False