from typing import Literal

from .state import MedicalResearchState


def route_after_citation_validation(
    state: MedicalResearchState,
) -> Literal["release", "block"]:
    if state.get("validation_status") == "valid":
        return "release"

    return "block"


def release_response(state: MedicalResearchState) -> dict:
    synthesis = state.get("synthesis")

    if not synthesis:
        return {
            "final_answer": (
                "The workflow could not produce a releasable evidence summary."
            ),
            "release_status": "blocked",
            "response_mode": "abstain",
            "errors": [
                {
                    "node": "release_response",
                    "code": "MISSING_RENDERED_SYNTHESIS",
                    "message": "Citation validation passed but synthesis was empty.",
                    "retryable": False,
                }
            ],
        }

    return {
        "final_answer": synthesis,
        "release_status": "released",
    }


def block_response(state: MedicalResearchState) -> dict:
    return {
        "final_answer": (
            "I cannot provide the evidence summary because its citations "
            "could not be validated against the retrieved evidence."
        ),
        "release_status": "blocked",
        "response_mode": "abstain",
    }