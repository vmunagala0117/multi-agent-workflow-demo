from .state import MedicalResearchState
from typing import Literal

def literature_research(
    state: MedicalResearchState,
) -> dict:
    """Simulate retrieving evidence from external literature."""
    return {
        "literature_results": [
            {
                "source_id": "literature-001",
                "source_type": "literature",
                "title": "Synthetic external research article",
                "content": f"External evidence related to: {state['user_query']}",
                "citation_label": "[LIT-001]",
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
                "source_type": "internal",
                "title": "Synthetic internal evidence document",
                "content": f"Internal evidence related to: {state['user_query']}",
                "citation_label": "[INT-001]",
            }
        ]
    }


def synthesize(state: MedicalResearchState) -> dict:
    literature_count = len(state["literature_results"])
    internal_count = len(state["internal_evidence"])

    prefix = (
        "PARTIAL EVIDENCE: "
        if state["response_mode"] == "partial"
        else ""
    )

    return {
        "synthesis": (
            f"{prefix}"
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

def assess_evidence(state: MedicalResearchState) -> dict:
    """Apply deterministic risk and evidence-completeness policy."""

    has_literature = bool(state["literature_results"])
    has_internal = bool(state["internal_evidence"])

    if has_literature and has_internal:
        return {
            "evidence_status": "complete",
            "response_mode": "full",
        }

    if has_literature or has_internal:
        response_mode = (
            "partial"
            if state["risk_level"] == "low"
            else "abstain"
        )

        return {
            "evidence_status": "partial",
            "response_mode": response_mode,
        }

    return {
        "evidence_status": "none",
        "response_mode": "abstain",
    }


def route_after_assessment(
    state: MedicalResearchState,
) -> Literal["synthesize", "abstain"]:
    """Select the next node from the deterministic policy result."""

    if state["response_mode"] in {"full", "partial"}:
        return "synthesize"

    return "abstain"


def abstain(state: MedicalResearchState) -> dict:
    """Return a safe response when required evidence is unavailable."""

    available_citations = [
        *state["literature_results"],
        *state["internal_evidence"],
    ]

    return {
        "synthesis": (
            "Insufficient evidence is available to provide a reliable "
            "response for this request."
        ),
        "citations": available_citations,
        "validation_status": "insufficient_evidence",
    }