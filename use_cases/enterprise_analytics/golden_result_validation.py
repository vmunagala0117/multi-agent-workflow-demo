import json
from decimal import Decimal, InvalidOperation
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


def _numeric_equal(left: Any, right: Any) -> bool:
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, TypeError, ValueError):
        return False


def validate_against_golden_contract(
    *,
    plan: AnalyticsQueryPlan,
    observed_result: dict[str, Any],
) -> list[str]:
    expected = _expected_result(plan)

    if plan.question_class == QuestionClass.FINANCE_VARIANCE:
        numeric_keys = (
            "actual_expense",
            "budget_expense",
            "variance_amount",
            "variance_percent",
        )

        valid = all(
            _numeric_equal(
                observed_result.get(key),
                expected.get(key),
            )
            for key in numeric_keys
        )

    elif (
        plan.question_class
        == QuestionClass.BUSINESS_UNIT_CONTRIBUTION
    ):
        observed_items = observed_result.get(
            "contributions",
            [],
        )
        expected_items = expected.get(
            "ranked_contributions",
            [],
        )

        valid = (
            len(observed_items) == len(expected_items)
            and all(
                observed_item.get("business_unit_id")
                == expected_item.get("business_unit_id")
                and _numeric_equal(
                    observed_item.get("variance_amount"),
                    expected_item.get("variance_amount"),
                )
                for observed_item, expected_item in zip(
                    observed_items,
                    expected_items,
                    strict=True,
                )
            )
        )

    else:
        numeric_keys = (
            "volume_effect",
            "rate_effect",
            "total_variance",
        )

        valid = all(
            _numeric_equal(
                observed_result.get(key),
                expected.get(key),
            )
            for key in numeric_keys
        ) and (
            observed_result.get("primary_driver")
            == expected.get("primary_driver")
        )

    if valid:
        return []

    return [
        "Observed result does not match the independent "
        "golden contract"
    ]