import csv
from decimal import Decimal
from pathlib import Path

DATA_DIR = (
    Path(__file__).parents[3]
    / "use_cases"
    / "enterprise_analytics"
    / "data"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finance_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row["period"],
        row["business_unit_id"],
        row["cost_category"],
    )


def test_finance_actual_and_budget_keys_match() -> None:
    actual_keys = {finance_key(row) for row in read_csv("finance_actuals.csv")}
    budget_keys = {finance_key(row) for row in read_csv("finance_budget.csv")}

    assert actual_keys == budget_keys


def test_all_business_unit_references_are_valid() -> None:
    valid_ids = {
        row["business_unit_id"]
        for row in read_csv("business_units.csv")
    }

    referenced_ids = {
        row["business_unit_id"]
        for name in (
            "finance_actuals.csv",
            "finance_budget.csv",
            "operations_metrics.csv",
        )
        for row in read_csv(name)
    }

    assert referenced_ids <= valid_ids


def test_august_southeast_finance_ground_truth() -> None:
    southeast_ids = {
        row["business_unit_id"]
        for row in read_csv("business_units.csv")
        if row["region"] == "Southeast"
    }

    actual_by_key = {
        finance_key(row): Decimal(row["actual_expense"])
        for row in read_csv("finance_actuals.csv")
    }
    budget_by_key = {
        finance_key(row): Decimal(row["budget_expense"])
        for row in read_csv("finance_budget.csv")
    }

    target_keys = {
        key
        for key in actual_by_key
        if key[0] == "2026-08"
        and key[1] in southeast_ids
        and key[2] == "logistics_expense"
    }

    actual = sum(actual_by_key[key] for key in target_keys)
    budget = sum(budget_by_key[key] for key in target_keys)
    variance = actual - budget

    assert actual == Decimal("1330000")
    assert budget == Decimal("1180000")
    assert variance == Decimal("150000")
    assert (variance / budget * 100).quantize(Decimal("0.01")) == Decimal(
        "12.71"
    )


def test_business_unit_variance_contributions() -> None:
    actual_by_key = {
        finance_key(row): Decimal(row["actual_expense"])
        for row in read_csv("finance_actuals.csv")
    }
    budget_by_key = {
        finance_key(row): Decimal(row["budget_expense"])
        for row in read_csv("finance_budget.csv")
    }

    contributions = {
        business_unit_id: (
            actual_by_key[("2026-08", business_unit_id, "logistics_expense")]
            - budget_by_key[("2026-08", business_unit_id, "logistics_expense")]
        )
        for business_unit_id in ("BU-101", "BU-102", "BU-103")
    }

    assert contributions == {
        "BU-101": Decimal("100000"),
        "BU-102": Decimal("30000"),
        "BU-103": Decimal("20000"),
    }


def test_operations_reconcile_to_finance() -> None:
    actual_by_key = {
        finance_key(row): Decimal(row["actual_expense"])
        for row in read_csv("finance_actuals.csv")
    }
    budget_by_key = {
        finance_key(row): Decimal(row["budget_expense"])
        for row in read_csv("finance_budget.csv")
    }

    for row in read_csv("operations_metrics.csv"):
        key = (
            row["period"],
            row["business_unit_id"],
            "logistics_expense",
        )
        calculated_actual = (
            Decimal(row["actual_shipment_volume"])
            * Decimal(row["actual_cost_per_shipment"])
        )
        calculated_budget = (
            Decimal(row["budget_shipment_volume"])
            * Decimal(row["budget_cost_per_shipment"])
        )

        assert calculated_actual == actual_by_key[key]
        assert calculated_budget == budget_by_key[key]


def test_cost_per_shipment_is_primary_variance_driver() -> None:
    volume_effect = Decimal("0")
    rate_effect = Decimal("0")

    for row in read_csv("operations_metrics.csv"):
        actual_volume = Decimal(row["actual_shipment_volume"])
        budget_volume = Decimal(row["budget_shipment_volume"])
        actual_rate = Decimal(row["actual_cost_per_shipment"])
        budget_rate = Decimal(row["budget_cost_per_shipment"])

        volume_effect += (actual_volume - budget_volume) * budget_rate
        rate_effect += actual_volume * (actual_rate - budget_rate)

    assert volume_effect == Decimal("15000")
    assert rate_effect == Decimal("135000")
    assert volume_effect + rate_effect == Decimal("150000")
    assert rate_effect > volume_effect
