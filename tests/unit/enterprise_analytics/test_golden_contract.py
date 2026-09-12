import json
from decimal import Decimal
from pathlib import Path

import pytest

from use_cases.enterprise_analytics.reference_calculator import (
    calculate_finance_variance,
    calculate_operations_driver,
)


GOLDEN_PATH = (
    Path(__file__).parents[3]
    / "evals"
    / "enterprise_analytics"
    / "golden_cases.json"
)


def load_cases() -> list[dict]:
    payload = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert payload["version"] == "1.0.0"
    return payload["cases"]


def test_golden_case_ids_are_unique() -> None:
    case_ids = [case["case_id"] for case in load_cases()]
    assert len(case_ids) == len(set(case_ids))


def test_all_supported_question_classes_are_covered() -> None:
    assert {
        case["expected_question_class"] for case in load_cases()
    } == {
        "finance_variance",
        "business_unit_contribution",
        "operations_driver",
    }


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: case["case_id"])
def test_golden_case_expected_result_is_reproducible(case: dict) -> None:
    expected = case["expected_result"]
    filters = case["filters"]

    if case["expected_question_class"] == "operations_driver":
        result = calculate_operations_driver(
            period=filters["period"],
            region=filters["region"],
        )
        assert result.volume_effect == Decimal(expected["volume_effect"])
        assert result.rate_effect == Decimal(expected["rate_effect"])
        assert result.total_variance == Decimal(expected["total_variance"])
        assert result.primary_driver == expected["primary_driver"]
        return

    result = calculate_finance_variance(
        period=filters["period"],
        region=filters["region"],
        cost_category=filters["cost_category"],
    )

    if case["expected_question_class"] == "finance_variance":
        assert result.actual_expense == Decimal(expected["actual_expense"])
        assert result.budget_expense == Decimal(expected["budget_expense"])
        assert result.variance_amount == Decimal(expected["variance_amount"])
        assert result.variance_percent == Decimal(expected["variance_percent"])
        return

    actual_contributions = [
        {
            "business_unit_id": item.business_unit_id,
            "variance_amount": item.variance_amount,
        }
        for item in result.contributions
    ]
    expected_contributions = [
        {
            "business_unit_id": item["business_unit_id"],
            "variance_amount": Decimal(item["variance_amount"]),
        }
        for item in expected["ranked_contributions"]
    ]
    assert actual_contributions == expected_contributions