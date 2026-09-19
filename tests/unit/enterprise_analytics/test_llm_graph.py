from typing import Any

import pytest

from use_cases.enterprise_analytics.live_graph import (
    build_live_enterprise_analytics_graph,
)
from use_cases.enterprise_analytics.llm_reasoning import (
    GroundedNarrative,
    SemanticIntent,
)
from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    FilterCondition,
    MetricName,
    QuestionClass,
)

from use_cases.enterprise_analytics.live_graph import (
    bind_plan_to_classified_scope,
    build_live_enterprise_analytics_graph,
)


class FakeReasoner:
    def __init__(
        self,
        *,
        answer: str,
        change_scope: bool = False,
    ) -> None:
        self.answer = answer
        self.change_scope = change_scope

    async def classify(self, user_query: str) -> SemanticIntent:
        return SemanticIntent(
            supported=True,
            question_class=QuestionClass.FINANCE_VARIANCE,
            period="2026-08",
            region="Southeast",
            cost_category="logistics_expense",
        )

    async def plan(
        self,
        *,
        user_query: str,
        intent: SemanticIntent,
        skill_instructions: str,
        dataset_schema: dict[str, Any],
        metric_definitions: list[dict[str, Any]],
    ) -> AnalyticsQueryPlan:
        region = "Northeast" if self.change_scope else intent.region
        return AnalyticsQueryPlan(
            domain=AnalyticsDomain.FINANCE,
            question_class=QuestionClass.FINANCE_VARIANCE,
            metrics=[
                MetricName.ACTUAL_EXPENSE,
                MetricName.BUDGET_EXPENSE,
                MetricName.VARIANCE_AMOUNT,
                MetricName.VARIANCE_PERCENT,
            ],
            dimensions=[],
            filters=[
                FilterCondition(field="period", value=intent.period),
                FilterCondition(field="region", value=region),
                FilterCondition(
                    field="cost_category",
                    value=intent.cost_category,
                ),
            ],
            row_limit=100,
        )

    async def synthesize(
        self,
        *,
        user_query: str,
        skill_instructions: str,
        validated_result: dict[str, Any],
    ) -> GroundedNarrative:
        return GroundedNarrative(answer=self.answer)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def run_graph(reasoner: FakeReasoner):
    graph = build_live_enterprise_analytics_graph(reasoner=reasoner)
    return await graph.ainvoke(
        {
            "user_query": (
                "Could you break down how Southeast logistics spending "
                "performed against plan for August 2026?"
            ),
            "user_id": "demo-finance-user",
            "status": "received",
            "tool_trajectory": [],
        }
    )


@pytest.mark.anyio
async def test_structured_reasoner_releases_grounded_answer() -> None:
    result = await run_graph(
        FakeReasoner(
            answer=(
                "Southeast logistics expense was $150,000.00 over budget, "
                "an unfavorable variance of 12.71%."
            )
        )
    )

    assert result["status"] == "completed"
    assert result["result_valid"] is True
    assert result["claim_validation_errors"] == []
    assert "$150,000.00" in result["final_answer"]


@pytest.mark.anyio
async def test_hallucinated_numeric_claim_is_blocked() -> None:
    result = await run_graph(
        FakeReasoner(
            answer=(
                "Southeast logistics expense was $999,999.00 over budget."
            )
        )
    )

    assert result["status"] == "clarification_required"
    assert result["final_answer"] is None
    assert "unsupported monetary claims" in result["error"]


@pytest.mark.anyio
async def test_changed_scope_plan_fails_before_mcp_execution() -> None:
    with pytest.raises(ValueError, match="changed the classified request scope"):
        await run_graph(
            FakeReasoner(
                answer="The validated variance was $150,000.00.",
                change_scope=True,
            )
        )

def test_operations_plan_drops_irrelevant_cost_category_filter() -> None:
    plan = AnalyticsQueryPlan(
        domain=AnalyticsDomain.OPERATIONS,
        question_class=QuestionClass.OPERATIONS_DRIVER,
        metrics=[
            MetricName.ACTUAL_SHIPMENT_VOLUME,
            MetricName.BUDGET_SHIPMENT_VOLUME,
            MetricName.ACTUAL_COST_PER_SHIPMENT,
            MetricName.BUDGET_COST_PER_SHIPMENT,
            MetricName.VOLUME_EFFECT,
            MetricName.RATE_EFFECT,
        ],
        dimensions=[],
        filters=[
            FilterCondition(
                field="period",
                value="2026-08",
            ),
            FilterCondition(
                field="region",
                value="Southeast",
            ),
            FilterCondition(
                field="cost_category",
                value="logistics_expense",
            ),
        ],
        row_limit=100,
    )

    bound = bind_plan_to_classified_scope(
        plan=plan,
        state={
            "question_class": QuestionClass.OPERATIONS_DRIVER,
            "period": "2026-08",
            "region": "Southeast",
        },
    )

    assert [item.field for item in bound.filters] == [
        "period",
        "region",
    ]