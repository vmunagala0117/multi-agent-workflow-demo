import csv
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel


DATA_DIR = Path(__file__).parent / "data"
MONEY_PLACES = Decimal("0.01")
PERCENT_PLACES = Decimal("0.01")


class BusinessUnitContribution(BaseModel):
    business_unit_id: str
    business_unit_name: str
    actual_expense: Decimal
    budget_expense: Decimal
    variance_amount: Decimal


class FinanceVarianceResult(BaseModel):
    period: str
    region: str
    cost_category: str
    actual_expense: Decimal
    budget_expense: Decimal
    variance_amount: Decimal
    variance_percent: Decimal | None
    contributions: list[BusinessUnitContribution]


class OperationsDriverResult(BaseModel):
    period: str
    region: str
    volume_effect: Decimal
    rate_effect: Decimal
    total_variance: Decimal
    primary_driver: str


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _finance_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row["period"],
        row["business_unit_id"],
        row["cost_category"],
    )


def calculate_finance_variance(
    *,
    period: str,
    region: str,
    cost_category: str,
) -> FinanceVarianceResult:
    units = {
        row["business_unit_id"]: row
        for row in _read_csv("business_units.csv")
    }
    budgets = {
        _finance_key(row): Decimal(row["budget_expense"])
        for row in _read_csv("finance_budget.csv")
    }

    contributions: list[BusinessUnitContribution] = []

    for row in _read_csv("finance_actuals.csv"):
        unit = units[row["business_unit_id"]]
        if (
            row["period"] != period
            or unit["region"] != region
            or row["cost_category"] != cost_category
        ):
            continue

        key = _finance_key(row)
        if key not in budgets:
            raise ValueError(f"Missing budget row for {key}")

        actual = Decimal(row["actual_expense"])
        budget = budgets[key]
        contributions.append(
            BusinessUnitContribution(
                business_unit_id=row["business_unit_id"],
                business_unit_name=unit["business_unit_name"],
                actual_expense=actual,
                budget_expense=budget,
                variance_amount=actual - budget,
            )
        )

    if not contributions:
        raise ValueError(
            "No finance data matched the requested period, region, and category"
        )

    contributions.sort(
        key=lambda item: item.variance_amount,
        reverse=True,
    )
    actual_total = sum(
        item.actual_expense for item in contributions
    ).quantize(MONEY_PLACES)
    budget_total = sum(
        item.budget_expense for item in contributions
    ).quantize(MONEY_PLACES)
    variance = (actual_total - budget_total).quantize(MONEY_PLACES)
    variance_percent = (
        None
        if budget_total == 0
        else (variance / budget_total * 100).quantize(PERCENT_PLACES)
    )

    return FinanceVarianceResult(
        period=period,
        region=region,
        cost_category=cost_category,
        actual_expense=actual_total,
        budget_expense=budget_total,
        variance_amount=variance,
        variance_percent=variance_percent,
        contributions=contributions,
    )


def calculate_operations_driver(
    *,
    period: str,
    region: str,
) -> OperationsDriverResult:
    units = {
        row["business_unit_id"]: row
        for row in _read_csv("business_units.csv")
    }
    volume_effect = Decimal("0")
    rate_effect = Decimal("0")
    matched_rows = 0

    for row in _read_csv("operations_metrics.csv"):
        unit = units[row["business_unit_id"]]
        if row["period"] != period or unit["region"] != region:
            continue

        matched_rows += 1
        actual_volume = Decimal(row["actual_shipment_volume"])
        budget_volume = Decimal(row["budget_shipment_volume"])
        actual_rate = Decimal(row["actual_cost_per_shipment"])
        budget_rate = Decimal(row["budget_cost_per_shipment"])

        volume_effect += (actual_volume - budget_volume) * budget_rate
        rate_effect += actual_volume * (actual_rate - budget_rate)

    if matched_rows == 0:
        raise ValueError(
            "No operations data matched the requested period and region"
        )

    volume_effect = volume_effect.quantize(MONEY_PLACES)
    rate_effect = rate_effect.quantize(MONEY_PLACES)
    total_variance = (volume_effect + rate_effect).quantize(MONEY_PLACES)

    finance_result = calculate_finance_variance(
        period=period,
        region=region,
        cost_category="logistics_expense",
    )
    if total_variance != finance_result.variance_amount:
        raise ValueError(
            "Operations driver effects do not reconcile to finance variance"
        )

    primary_driver = (
        "cost_per_shipment"
        if abs(rate_effect) > abs(volume_effect)
        else "shipment_volume"
    )

    return OperationsDriverResult(
        period=period,
        region=region,
        volume_effect=volume_effect,
        rate_effect=rate_effect,
        total_variance=total_variance,
        primary_driver=primary_driver,
    )