import re
from decimal import Decimal
from typing import Any

from use_cases.enterprise_analytics.schemas import QuestionClass


MONEY_PATTERN = re.compile(r"\$([0-9][0-9,]*(?:\.\d+)?)")
PERCENT_PATTERN = re.compile(r"([0-9]+(?:\.\d+)?)%")
MONEY_KEYS = {
    "actual_expense",
    "budget_expense",
    "variance_amount",
    "volume_effect",
    "rate_effect",
    "total_variance",
}


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value).replace(",", ""))


def _allowed_money_values(value: Any) -> set[Decimal]:
    allowed: set[Decimal] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in MONEY_KEYS and item is not None:
                allowed.add(_decimal(item))
            allowed.update(_allowed_money_values(item))
    elif isinstance(value, list):
        for item in value:
            allowed.update(_allowed_money_values(item))
    return allowed


def validate_numeric_claims(
    *,
    answer: str,
    result: dict[str, Any],
    question_class: QuestionClass,
) -> list[str]:
    errors: list[str] = []
    money_claims = {
        _decimal(match) for match in MONEY_PATTERN.findall(answer)
    }
    percent_claims = {
        _decimal(match) for match in PERCENT_PATTERN.findall(answer)
    }
    allowed_money = _allowed_money_values(result)
    allowed_percent = (
        {_decimal(result["variance_percent"])}
        if result.get("variance_percent") is not None
        else set()
    )

    unsupported_money = money_claims - allowed_money
    unsupported_percent = percent_claims - allowed_percent
    if unsupported_money:
        errors.append(
            "Narrative contains unsupported monetary claims: "
            + ", ".join(str(value) for value in sorted(unsupported_money))
        )
    if unsupported_percent:
        errors.append(
            "Narrative contains unsupported percentage claims: "
            + ", ".join(str(value) for value in sorted(unsupported_percent))
        )

    required_value = (
        _decimal(result["total_variance"])
        if question_class == QuestionClass.OPERATIONS_DRIVER
        else _decimal(result["variance_amount"])
    )
    if required_value not in money_claims:
        errors.append("Narrative omitted the validated variance amount")

    return errors