from operator import add
from typing import Annotated, Any, Literal, TypedDict

from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    QuestionClass,
)


WorkflowStatus = Literal[
    "received",
    "classified",
    "clarification_required",
    "authorized",
    "access_denied",
    "skill_loaded",
    "context_loaded",
    "planned",
    "plan_validated",
    "executed",
    "result_validated",
    "completed",
]


class EnterpriseAnalyticsState(TypedDict, total=False):
    user_query: str
    user_id: str
    status: WorkflowStatus

    question_class: QuestionClass
    period: str
    region: str
    cost_category: str

    allowed_domains: set[AnalyticsDomain]
    selected_skill_name: str
    selected_skill_version: str
    selected_skill_instructions: str
    allowed_tools: set[str]

    dataset_schema: dict[str, Any]
    metric_definitions: list[dict[str, Any]]
    query_plan: AnalyticsQueryPlan
    validation_id: str
    analytics_result: dict[str, Any]
    result_valid: bool
    validation_errors: list[str]

    tool_trajectory: Annotated[list[str], add]
    final_answer: str | None
    error: str | None