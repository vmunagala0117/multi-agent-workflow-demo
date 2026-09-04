import operator
from typing import Annotated, TypedDict


class WorkflowError(TypedDict):
    node: str
    code: str
    message: str
    retryable: bool


class MedicalResearchState(TypedDict):
    user_query: str

    literature_results: list[dict]
    internal_evidence: list[dict]

    synthesis: str | None
    citations: list[dict]

    validation_status: str | None

    errors: Annotated[list[WorkflowError], operator.add]