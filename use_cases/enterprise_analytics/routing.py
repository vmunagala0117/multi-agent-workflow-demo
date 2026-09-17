from pydantic import BaseModel, ConfigDict

from use_cases.enterprise_analytics.schemas import QuestionClass


class IntentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supported: bool
    question_class: QuestionClass | None = None
    period: str | None = None
    region: str | None = None
    cost_category: str | None = None
    clarification: str | None = None


def classify_intent(user_query: str) -> IntentDecision:
    normalized = " ".join(user_query.lower().split())

    period = (
        "2026-08"
        if "august" in normalized or "2026-08" in normalized
        else None
    )
    region = "Southeast" if "southeast" in normalized else None

    if "shipment" in normalized or "cost per shipment" in normalized:
        question_class = QuestionClass.OPERATIONS_DRIVER
        cost_category = None
    elif (
        "which business unit" in normalized
        or "business units" in normalized
        or "contributed most" in normalized
    ):
        question_class = QuestionClass.BUSINESS_UNIT_CONTRIBUTION
        cost_category = "logistics_expense"
    elif "budget" in normalized and (
        "variance" in normalized or "exceed" in normalized
    ):
        question_class = QuestionClass.FINANCE_VARIANCE
        cost_category = "logistics_expense"
    else:
        return IntentDecision(
            supported=False,
            clarification=(
                "Ask about finance variance, business-unit contribution, "
                "or shipment volume versus cost-per-shipment drivers."
            ),
        )

    missing = []
    if period is None:
        missing.append("reporting period")
    if region is None:
        missing.append("region")
    if missing:
        return IntentDecision(
            supported=False,
            clarification="Please provide the " + " and ".join(missing) + ".",
        )

    return IntentDecision(
        supported=True,
        question_class=question_class,
        period=period,
        region=region,
        cost_category=cost_category,
    )