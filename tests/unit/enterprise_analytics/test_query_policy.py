from datetime import UTC, datetime, timedelta

import pytest

from use_cases.enterprise_analytics.mcp_server.query_service import (
    QueryService,
)
from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    FilterCondition,
    MetricName,
    QuestionClass,
)


def finance_plan(**overrides) -> AnalyticsQueryPlan:
    payload = {
        "domain": AnalyticsDomain.FINANCE,
        "question_class": QuestionClass.FINANCE_VARIANCE,
        "metrics": [
            MetricName.ACTUAL_EXPENSE,
            MetricName.BUDGET_EXPENSE,
            MetricName.VARIANCE_AMOUNT,
            MetricName.VARIANCE_PERCENT,
        ],
        "dimensions": [],
        "filters": [
            FilterCondition(field="period", value="2026-08"),
            FilterCondition(field="region", value="Southeast"),
            FilterCondition(
                field="cost_category",
                value="logistics_expense",
            ),
        ],
        "row_limit": 100,
    }
    payload.update(overrides)
    return AnalyticsQueryPlan(**payload)


def test_rejects_malformed_period() -> None:
    plan = finance_plan(
        filters=[
            FilterCondition(field="period", value="August 2026"),
            FilterCondition(field="region", value="Southeast"),
            FilterCondition(
                field="cost_category",
                value="logistics_expense",
            ),
        ]
    )

    with pytest.raises(ValueError, match="YYYY-MM"):
        QueryService().validate(
            user_id="demo-finance-user",
            plan=plan,
        )


def test_rejects_injection_like_region_value() -> None:
    plan = finance_plan(
        filters=[
            FilterCondition(field="period", value="2026-08"),
            FilterCondition(
                field="region",
                value="Southeast' OR 1=1 --",
            ),
            FilterCondition(
                field="cost_category",
                value="logistics_expense",
            ),
        ]
    )

    with pytest.raises(ValueError, match="region"):
        QueryService().validate(
            user_id="demo-finance-user",
            plan=plan,
        )


def test_rejects_unsupported_cost_category() -> None:
    plan = finance_plan(
        filters=[
            FilterCondition(field="period", value="2026-08"),
            FilterCondition(field="region", value="Southeast"),
            FilterCondition(field="cost_category", value="payroll"),
        ]
    )

    with pytest.raises(ValueError, match="cost_category"):
        QueryService().validate(
            user_id="demo-finance-user",
            plan=plan,
        )


def test_rejects_policy_row_limit_excess() -> None:
    with pytest.raises(ValueError, match="policy maximum"):
        QueryService().validate(
            user_id="demo-finance-user",
            plan=finance_plan(row_limit=101),
        )


def test_rejects_unknown_filter_field() -> None:
    plan = finance_plan(
        filters=[
            FilterCondition(field="period", value="2026-08"),
            FilterCondition(field="region", value="Southeast"),
            FilterCondition(
                field="cost_category",
                value="logistics_expense",
            ),
            FilterCondition(field="employee_ssn", value="*"),
        ]
    )

    with pytest.raises(ValueError, match="unsupported filters"):
        QueryService().validate(
            user_id="demo-finance-user",
            plan=plan,
        )


def test_expired_validation_receipt_cannot_execute() -> None:
    current = [datetime(2026, 9, 18, 12, 0, tzinfo=UTC)]
    service = QueryService(clock=lambda: current[0])
    receipt = service.validate(
        user_id="demo-finance-user",
        plan=finance_plan(),
    )

    assert receipt.policy_version == "1.0.0"
    assert receipt.plan_hash

    current[0] += timedelta(minutes=6)

    with pytest.raises(ValueError, match="Unknown or expired"):
        service.execute(
            user_id="demo-finance-user",
            validation_id=receipt.validation_id,
        )
def test_authorization_precedes_policy_details() -> None:
    malformed = finance_plan(
        filters=[
            FilterCondition(field="period", value="not-a-period"),
            FilterCondition(field="region", value="Southeast"),
            FilterCondition(
                field="cost_category",
                value="logistics_expense",
            ),
        ]
    )

    with pytest.raises(PermissionError, match="not authorized"):
        QueryService().validate(
            user_id="demo-unauthorized-user",
            plan=malformed,
        )


def test_mutated_receipt_plan_fails_binding_check() -> None:
    service = QueryService()
    receipt = service.validate(
        user_id="demo-finance-user",
        plan=finance_plan(),
    )
    receipt.plan.filters[0].value = "2026-07"

    with pytest.raises(ValueError, match="plan binding"):
        service.execute(
            user_id="demo-finance-user",
            validation_id=receipt.validation_id,
        )


def test_tampered_result_fails_independent_golden_validation() -> None:
    service = QueryService()
    receipt = service.validate(
        user_id="demo-finance-user",
        plan=finance_plan(),
    )
    executed = service.execute(
        user_id="demo-finance-user",
        validation_id=receipt.validation_id,
    )
    tampered = dict(executed.data)
    tampered["variance_amount"] = "999999.00"

    checked = service.validate_result(
        user_id="demo-finance-user",
        validation_id=receipt.validation_id,
        observed_result=tampered,
    )

    assert checked.valid is False
    assert "independent golden contract" in checked.errors[0]

def test_rejects_missing_required_metric() -> None:
    plan = finance_plan(
        metrics=[
            MetricName.ACTUAL_EXPENSE,
            MetricName.BUDGET_EXPENSE,
            MetricName.VARIANCE_AMOUNT,
        ]
    )

    with pytest.raises(ValueError, match="governed question contract"):
        QueryService().validate(
            user_id="demo-finance-user",
            plan=plan,
        )