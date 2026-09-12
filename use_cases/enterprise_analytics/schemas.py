from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalyticsDomain(StrEnum):
    FINANCE = "finance"
    OPERATIONS = "operations"


class QuestionClass(StrEnum):
    FINANCE_VARIANCE = "finance_variance"
    BUSINESS_UNIT_CONTRIBUTION = "business_unit_contribution"
    OPERATIONS_DRIVER = "operations_driver"


class MetricName(StrEnum):
    ACTUAL_EXPENSE = "actual_expense"
    BUDGET_EXPENSE = "budget_expense"
    VARIANCE_AMOUNT = "variance_amount"
    VARIANCE_PERCENT = "variance_percent"
    ACTUAL_SHIPMENT_VOLUME = "actual_shipment_volume"
    BUDGET_SHIPMENT_VOLUME = "budget_shipment_volume"
    ACTUAL_COST_PER_SHIPMENT = "actual_cost_per_shipment"
    BUDGET_COST_PER_SHIPMENT = "budget_cost_per_shipment"
    VOLUME_EFFECT = "volume_effect"
    RATE_EFFECT = "rate_effect"

class AggregationRule(StrEnum):
    SUM = "sum"
    WEIGHTED_AVERAGE = "weighted_average"
    DERIVED = "derived"


class FavorableDirection(StrEnum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"
    NEUTRAL = "neutral"


class MetricDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: MetricName
    domain: AnalyticsDomain
    business_name: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    aggregation: AggregationRule
    source_fields: list[str] = Field(min_length=1)
    formula: str | None = None
    allowed_dimensions: set[str] = Field(min_length=1)
    favorable_direction: FavorableDirection
    guardrails: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_formula_for_calculated_metrics(self) -> "MetricDefinition":
        calculated_rules = {
            AggregationRule.DERIVED,
            AggregationRule.WEIGHTED_AVERAGE,
        }
        if self.aggregation in calculated_rules and not self.formula:
            raise ValueError(
                f"{self.metric_id} requires an explicit formula"
            )
        return self


class SemanticCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    metrics: list[MetricDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_metric_ids(self) -> "SemanticCatalog":
        metric_ids = [metric.metric_id for metric in self.metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("metric_id values must be unique")
        return self

class FilterCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    value: str


class AnalyticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_query: str = Field(min_length=5)
    user_id: str = Field(min_length=1)
    allowed_domains: set[AnalyticsDomain] = Field(default_factory=set)


class AnalyticsQueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: AnalyticsDomain
    question_class: QuestionClass
    metrics: list[MetricName] = Field(min_length=1)
    dimensions: list[str] = Field(default_factory=list)
    filters: list[FilterCondition] = Field(default_factory=list)
    row_limit: int = Field(default=100, ge=1, le=500)

    @model_validator(mode="after")
    def validate_domain_question_alignment(self) -> "AnalyticsQueryPlan":
        finance_questions = {
            QuestionClass.FINANCE_VARIANCE,
            QuestionClass.BUSINESS_UNIT_CONTRIBUTION,
        }

        if (
            self.question_class in finance_questions
            and self.domain != AnalyticsDomain.FINANCE
        ):
            raise ValueError(
                f"{self.question_class} must use the finance domain"
            )

        if (
            self.question_class == QuestionClass.OPERATIONS_DRIVER
            and self.domain != AnalyticsDomain.OPERATIONS
        ):
            raise ValueError(
                "operations_driver must use the operations domain"
            )

        return self