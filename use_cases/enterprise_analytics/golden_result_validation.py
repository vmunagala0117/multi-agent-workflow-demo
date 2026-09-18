import json
from pathlib import Path
from typing import Any

from use_cases.enterprise_analytics.schemas import (
    AnalyticsQueryPlan,
    QuestionClass,
)


GOLDEN_PATH = (
    Path(__file__).parents[2]
    / "evals"
    / "enterprise_analytics"
    / "golden_cases.json"
)


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(
        GOLDEN_PATH.read_text(encoding="utf-8")
    )
    return payload["cases"]


def _expected_result(
    plan: AnalyticsQueryPlan,
) -> dict[str, Any]:
    filters = {
        item.field: item.value
        for item in plan.filters
    }

    for case in _load_cases():
        if (
            case["expected_question_class"]
            == plan.question_class.value
            and case["filters"] == filters
        ):
            return case["expected_result"]

    raise ValueError(
        "No approved golden contract matches the validated query plan"
    )


def validate_against_golden_contract(
    *,
    plan: AnalyticsQueryPlan,
    observed_result: dict[str, Any],
) -> list[str]:
    expected = _expected_result(plan)

    if plan.question_class == QuestionClass.FINANCE_VARIANCE:
        observed = {
            key: observed_result.get(key)
            for key in (
                "actual_expense",
                "budget_expense",
                "variance_amount",
                "variance_percent",
            )
        }

    elif (
        plan.question_class
        == QuestionClass.BUSINESS_UNIT_CONTRIBUTION
    ):
        observed = {
            "ranked_contributions": [
                {
                    "business_unit_id": item.get(
                        "business_unit_id"
                    ),
                    "variance_amount": item.get(
                        "variance_amount"
                    ),
                }
                for item in observed_result.get(
                    "contributions",
                    [],
                )
            ]
        }

    else:
        observed = {
            key: observed_result.get(key)
            for key in (
                "volume_effect",
                "rate_effect",
                "total_variance",
                "primary_driver",
            )
        }

    if observed == expected:
        return []

    return [
        "Observed result does not match the independent "
        "golden contract"
    ]