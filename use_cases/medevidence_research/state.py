from typing import TypedDict


class MedicalResearchState(TypedDict):
    user_query: str
    literature_results: list[dict]
    internal_evidence: list[dict]
    synthesis: str | None
    citations: list[dict]
    validation_status: str | None
    errors: list[str]