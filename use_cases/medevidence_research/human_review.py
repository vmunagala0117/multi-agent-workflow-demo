from typing import Literal

from langgraph.types import interrupt

from .state import MedicalResearchState


def human_review(state: MedicalResearchState) -> dict:
    response = interrupt(
        {
            "review_type": "high_risk_medical_evidence",
            "question": "Approve this response for release?",
            "risk_level": state["risk_level"],
            "candidate_answer": state["synthesis"],
            "citation_labels": [
                record["citation_label"]
                for record in state["citations"]
            ],
        }
    )

    if not isinstance(response, dict):
        raise ValueError("Review response must be an object.")

    decision = response.get("decision")
    if decision not in {"approve", "reject"}:
        raise ValueError(
            "Review decision must be 'approve' or 'reject'."
        )

    return {
        "approval_status": (
            "approved" if decision == "approve" else "rejected"
        ),
        "reviewer_id": response.get("reviewer_id"),
        "review_comment": response.get("comment"),
    }


def route_after_review(
    state: MedicalResearchState,
) -> Literal["release", "reject"]:
    if state.get("approval_status") == "approved":
        return "release"

    return "reject"