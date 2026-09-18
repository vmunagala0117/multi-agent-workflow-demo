import re

from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    MetricName,
    QuestionClass,
)


POLICY_VERSION = "1.0.0"
MAX_DEMO_ROW_LIMIT = 100
PERIOD_PATTERN = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")

ALLOWED_FILTER_FIELDS = {
    AnalyticsDomain.FINANCE: {"period", "region", "cost_category"},
    AnalyticsDomain.OPERATIONS: {"period", "region"},
}
ALLOWED_REGIONS = {"Southeast", "Northeast"}
ALLOWED_COST_CATEGORIES = {"logistics_expense"}

REQUIRED_METRICS = {
    QuestionClass.FINANCE_VARIANCE: {
        MetricName.ACTUAL_EXPENSE,
        MetricName.BUDGET_EXPENSE,
        MetricName.VARIANCE_AMOUNT,
        MetricName.VARIANCE_PERCENT,
    },
    QuestionClass.BUSINESS_UNIT_CONTRIBUTION: {
        MetricName.ACTUAL_EXPENSE,
        MetricName.BUDGET_EXPENSE,
        MetricName.VARIANCE_AMOUNT,
        MetricName.VARIANCE_PERCENT,
    },
    QuestionClass.OPERATIONS_DRIVER: {
        MetricName.ACTUAL_SHIPMENT_VOLUME,
        MetricName.BUDGET_SHIPMENT_VOLUME,
        MetricName.ACTUAL_COST_PER_SHIPMENT,
        MetricName.BUDGET_COST_PER_SHIPMENT,
        MetricName.VOLUME_EFFECT,
        MetricName.RATE_EFFECT,
    },
}

def enforce_query_policy(plan: AnalyticsQueryPlan) -> None:
    if plan.row_limit > MAX_DEMO_ROW_LIMIT:
        raise ValueError(
            f"row_limit exceeds policy maximum {MAX_DEMO_ROW_LIMIT}"
        )

    if len(plan.dimensions) != len(set(plan.dimensions)):
        raise ValueError("Query plan contains duplicate dimensions")

    filter_fields = [item.field for item in plan.filters]
    if len(filter_fields) != len(set(filter_fields)):
        raise ValueError("Query plan contains duplicate filters")

    unsupported_fields = (
        set(filter_fields) - ALLOWED_FILTER_FIELDS[plan.domain]
    )
    if unsupported_fields:
        raise ValueError(
            "Query plan contains unsupported filters: "
            + ", ".join(sorted(unsupported_fields))
        )

    filters = {item.field: item.value for item in plan.filters}

    period = filters.get("period")
    if period is not None and not PERIOD_PATTERN.fullmatch(period):
        raise ValueError("period must use YYYY-MM format")

    region = filters.get("region")
    if region is not None and region not in ALLOWED_REGIONS:
        raise ValueError("region is outside the governed allowlist")

    cost_category = filters.get("cost_category")
    if (
        cost_category is not None
        and cost_category not in ALLOWED_COST_CATEGORIES
    ):
        raise ValueError(
            "cost_category is outside the governed allowlist"
        )

    required_metrics = REQUIRED_METRICS[plan.question_class]
    if set(plan.metrics) != required_metrics:
        raise ValueError(
            "Query plan metrics do not match the governed question contract"
        )