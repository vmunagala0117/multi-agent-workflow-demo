import operator
from typing import Annotated, Literal, TypedDict
from .models import EvidenceRecord
from .schemas import EvidenceSynthesis


class WorkflowError(TypedDict):
    node: str
    code: str
    message: str
    retryable: bool


class MedicalResearchState(TypedDict):
    user_query: str
    risk_level: Literal["low", "medium", "high"]

    literature_results: list[EvidenceRecord]
    internal_evidence: list[EvidenceRecord]

    evidence_status: Literal["complete", "partial", "none"] | None
    response_mode: Literal["full", "partial", "abstain"] | None

    synthesis: str | None
    synthesis_result: EvidenceSynthesis | None
    citations: list[dict]

    validation_status: str | None
    errors: Annotated[list[WorkflowError], operator.add]