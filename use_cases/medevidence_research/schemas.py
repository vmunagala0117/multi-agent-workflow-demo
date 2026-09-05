from pydantic import BaseModel, ConfigDict, Field


class CitedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding: str = Field(min_length=1)
    citation_labels: list[str] = Field(min_length=1)


class EvidenceSynthesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=1)
    efficacy_findings: list[CitedFinding]
    safety_findings: list[CitedFinding]
    evidence_gaps: list[str]
    limitations: list[str]