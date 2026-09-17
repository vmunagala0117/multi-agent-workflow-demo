from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    QuestionClass,
)


class AvailableDomains(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    domains: list[AnalyticsDomain]


class DatasetSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: AnalyticsDomain
    fact_sources: list[str] = Field(min_length=1)
    fields: list[str] = Field(min_length=1)
    dimensions: set[str] = Field(min_length=1)
    relationships: list[str] = Field(default_factory=list)


class QueryValidationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_id: str
    approved: bool
    user_id: str
    semantic_catalog_version: str
    plan: AnalyticsQueryPlan


class AnalyticsToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_id: str
    question_class: QuestionClass
    data: dict[str, Any]


class ResultValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation_id: str
    valid: bool
    errors: list[str] = Field(default_factory=list)