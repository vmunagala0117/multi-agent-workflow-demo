import operator
from typing import Annotated, Literal, TypedDict


class WorkflowError(TypedDict):
    node: str
    code: str
    message: str
    retryable: bool


class MedicalResearchState(TypedDict):
    user_query: str
    risk_level: Literal["low", "medium", "high"]

    literature_results: list[dict]
    internal_evidence: list[dict]

    evidence_status: Literal["complete", "partial", "none"] | None
    response_mode: Literal["full", "partial", "abstain"] | None

    synthesis: str | None
    citations: list[dict]

    validation_status: str | None
    errors: Annotated[list[WorkflowError], operator.add]