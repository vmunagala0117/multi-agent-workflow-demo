from .schemas import EvidenceSynthesis
from .state import MedicalResearchState


def validate_citations(state: MedicalResearchState) -> dict:
    result = state.get("synthesis_result")

    if result is None:
        return {
            "validation_status": "invalid",
            "errors": [
                {
                    "node": "validate_citations",
                    "code": "MISSING_SYNTHESIS_RESULT",
                    "message": "No structured synthesis result was available.",
                    "retryable": False,
                }
            ],
        }

    if not isinstance(result, EvidenceSynthesis):
        result = EvidenceSynthesis.model_validate(result)

    allowed_labels = {
        record["citation_label"]
        for record in [
            *state["literature_results"],
            *state["internal_evidence"],
        ]
    }

    cited_labels = {
        label
        for finding in [
            *result.efficacy_findings,
            *result.safety_findings,
        ]
        for label in finding.citation_labels
    }

    unknown_labels = sorted(cited_labels - allowed_labels)

    if unknown_labels:
        return {
            "validation_status": "invalid",
            "errors": [
                {
                    "node": "validate_citations",
                    "code": "UNKNOWN_CITATION_LABEL",
                    "message": (
                        "Synthesis referenced citation labels not present in "
                        f"workflow evidence: {', '.join(unknown_labels)}"
                    ),
                    "retryable": True,
                }
            ],
        }

    return {"validation_status": "valid"}