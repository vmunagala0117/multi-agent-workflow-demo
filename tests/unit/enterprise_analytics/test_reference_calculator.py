from decimal import Decimal

import pytest

from use_cases.enterprise_analytics.reference_calculator import (
    calculate_finance_variance,
    calculate_operations_driver,
)


def test_finance_variance_result_matches_ground_truth() -> None:
    result = calculate_finance_variance(
        period="2026-08",
        region="Southeast",
        cost_category="logistics_expense",
    )

    assert result.actual_expense == Decimal("1330000.00")
    assert result.budget_expense == Decimal("1180000.00")
    assert result.variance_amount == Decimal("150000.00")
    assert result.variance_percent == Decimal("12.71")


def test_business_unit_contributions_are_ranked() -> None:
    result = calculate_finance_variance(
        period="2026-08",
        region="Southeast",
        cost_category="logistics_expense",
    )

    assert [item.business_unit_id for item in result.contributions] == [
        "BU-101",
        "BU-102",
        "BU-103",
    ]
    assert [item.variance_amount for item in result.contributions] == [
        Decimal("100000"),
        Decimal("30000"),
        Decimal("20000"),
    ]


def test_operations_driver_reconciles_to_finance() -> None:
    result = calculate_operations_driver(
        period="2026-08",
        region="Southeast",
    )

    assert result.volume_effect == Decimal("15000.00")
    assert result.rate_effect == Decimal("135000.00")
    assert result.total_variance == Decimal("150000.00")
    assert result.primary_driver == "cost_per_shipment"


def test_unknown_slice_fails_instead_of_returning_zero() -> None:
    with pytest.raises(ValueError, match="No finance data matched"):
        calculate_finance_variance(
            period="2026-09",
            region="Southeast",
            cost_category="logistics_expense",
        )