import pytest
from pydantic import ValidationError

from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    AnalyticsRequest,
    MetricName,
    QuestionClass,
)


def test_valid_finance_request() -> None:
    request = AnalyticsRequest(
        user_query=(
            "Why did Southeast logistics expense exceed budget in August?"
        ),
        user_id="demo-finance-user",
        allowed_domains={AnalyticsDomain.FINANCE},
    )

    assert request.allowed_domains == {AnalyticsDomain.FINANCE}


def test_valid_finance_variance_plan() -> None:
    plan = AnalyticsQueryPlan(
        domain=AnalyticsDomain.FINANCE,
        question_class=QuestionClass.FINANCE_VARIANCE,
        metrics=[
            MetricName.ACTUAL_EXPENSE,
            MetricName.BUDGET_EXPENSE,
            MetricName.VARIANCE_AMOUNT,
        ],
        dimensions=["region", "month"],
        filters=[],
        row_limit=100,
    )

    assert plan.domain == AnalyticsDomain.FINANCE
    assert plan.row_limit == 100


def test_rejects_domain_question_mismatch() -> None:
    with pytest.raises(
        ValidationError,
        match="must use the finance domain",
    ):
        AnalyticsQueryPlan(
            domain=AnalyticsDomain.OPERATIONS,
            question_class=QuestionClass.FINANCE_VARIANCE,
            metrics=[MetricName.VARIANCE_AMOUNT],
        )


def test_rejects_unsupported_domain() -> None:
    with pytest.raises(ValidationError):
        AnalyticsRequest(
            user_query="Show clinical trial performance.",
            user_id="demo-user",
            allowed_domains={"clinical"},
        )


def test_rejects_unbounded_row_limit() -> None:
    with pytest.raises(ValidationError):
        AnalyticsQueryPlan(
            domain=AnalyticsDomain.FINANCE,
            question_class=QuestionClass.FINANCE_VARIANCE,
            metrics=[MetricName.VARIANCE_AMOUNT],
            row_limit=10_000,
        )


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AnalyticsQueryPlan(
            domain=AnalyticsDomain.FINANCE,
            question_class=QuestionClass.FINANCE_VARIANCE,
            metrics=[MetricName.VARIANCE_AMOUNT],
            raw_sql="DROP TABLE finance_actuals",
        )