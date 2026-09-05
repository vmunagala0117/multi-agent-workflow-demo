import pytest
from pydantic import ValidationError

from use_cases.medevidence_research.schemas import EvidenceSynthesis


def valid_payload() -> dict:
    return {
        "executive_summary": "Therapy Alpha reduced pruritus in the available evidence.",
        "efficacy_findings": [
            {
                "finding": "The pivotal trial reported improved pruritus outcomes.",
                "citation_labels": ["[LIT-001]"],
            }
        ],
        "safety_findings": [
            {
                "finding": "Long-term safety remains incompletely characterized.",
                "citation_labels": ["[INT-001]"],
            }
        ],
        "evidence_gaps": ["Limited evidence beyond one year."],
        "limitations": ["The local corpus is synthetic and intentionally small."],
    }


def test_valid_synthesis_payload_is_accepted() -> None:
    result = EvidenceSynthesis.model_validate(valid_payload())

    assert result.efficacy_findings[0].citation_labels == ["[LIT-001]"]


def test_finding_without_citation_is_rejected() -> None:
    payload = valid_payload()
    payload["efficacy_findings"][0]["citation_labels"] = []

    with pytest.raises(ValidationError):
        EvidenceSynthesis.model_validate(payload)


def test_unexpected_output_field_is_rejected() -> None:
    payload = valid_payload()
    payload["unsupported_field"] = "unexpected"

    with pytest.raises(ValidationError):
        EvidenceSynthesis.model_validate(payload)