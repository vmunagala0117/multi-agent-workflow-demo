from .state import MedicalResearchState
from typing import Literal

from .tools.retrieval import (
    search_internal_evidence,
    search_literature,
)

def literature_research(
    state: MedicalResearchState,
) -> dict:
    """Retrieve ranked evidence from the literature tool."""

    try:
        results = search_literature(
            query=state["user_query"],
            top_k=2,
        )
    except OSError as exc:
        return {
            "literature_results": [],
            "errors": [
                {
                    "node": "literature_research",
                    "code": "SOURCE_UNAVAILABLE",
                    "message": (
                        "The literature corpus could not be accessed. "
                        f"Error type: {type(exc).__name__}."
                    ),
                    "retryable": True,
                }
            ],
        }
    except ValueError as exc:
        return {
            "literature_results": [],
            "errors": [
                {
                    "node": "literature_research",
                    "code": "INVALID_RETRIEVAL_INPUT",
                    "message": (
                        "The literature request was invalid. "
                        f"Error type: {type(exc).__name__}."
                    ),
                    "retryable": False,
                }
            ],
        }

    return {"literature_results": results}


def internal_evidence(
    state: MedicalResearchState,
) -> dict:
    """Retrieve ranked evidence from the internal-evidence tool."""

    try:
        results = search_internal_evidence(
            query=state["user_query"],
            top_k=2,
        )
    except OSError as exc:
        return {
            "internal_evidence": [],
            "errors": [
                {
                    "node": "internal_evidence",
                    "code": "SOURCE_UNAVAILABLE",
                    "message": (
                        "The internal corpus could not be accessed. "
                        f"Error type: {type(exc).__name__}."
                    ),
                    "retryable": True,
                }
            ],
        }
    except ValueError as exc:
        return {
            "internal_evidence": [],
            "errors": [
                {
                    "node": "internal_evidence",
                    "code": "INVALID_RETRIEVAL_INPUT",
                    "message": (
                        "The internal-evidence request was invalid. "
                        f"Error type: {type(exc).__name__}."
                    ),
                    "retryable": False,
                }
            ],
        }

    return {"internal_evidence": results}


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