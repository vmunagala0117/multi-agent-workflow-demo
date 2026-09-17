import pytest

from use_cases.enterprise_analytics.graph import (
    build_enterprise_analytics_graph,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def run_graph(*, query: str, user_id: str):
    graph = build_enterprise_analytics_graph()
    return await graph.ainvoke(
        {
            "user_query": query,
            "user_id": user_id,
            "status": "received",
            "tool_trajectory": [],
        }
    )


@pytest.mark.anyio
async def test_finance_variance_completes_with_validated_result() -> None:
    result = await run_graph(
        query=(
            "Why did Southeast logistics expense exceed budget in August?"
        ),
        user_id="demo-finance-user",
    )

    assert result["status"] == "completed"
    assert result["analytics_result"]["variance_amount"] == "150000.00"
    assert "$150,000.00 unfavorable" in result["final_answer"]
    assert result["selected_skill_name"] == "finance_variance"
    assert result["result_valid"] is True
    assert result["tool_trajectory"][-3:] == [
        "validate_query",
        "execute_analytics_query",
        "validate_result",
    ]


@pytest.mark.anyio
async def test_business_unit_question_identifies_top_contributor() -> None:
    result = await run_graph(
        query=(
            "Which business units contributed most to the unfavorable "
            "Southeast logistics variance in August?"
        ),
        user_id="demo-finance-user",
    )

    assert result["status"] == "completed"
    assert "Regional Delivery" in result["final_answer"]
    assert "$100,000.00" in result["final_answer"]


@pytest.mark.anyio
async def test_operations_question_uses_operations_skill() -> None:
    result = await run_graph(
        query=(
            "Did shipment volume or cost per shipment drive the Southeast "
            "variance in August?"
        ),
        user_id="demo-analyst",
    )

    assert result["status"] == "completed"
    assert result["selected_skill_name"] == "operations_performance"
    assert result["analytics_result"]["primary_driver"] == (
        "cost_per_shipment"
    )
    assert "$135,000.00" in result["final_answer"]


@pytest.mark.anyio
async def test_finance_only_user_cannot_run_operations_skill() -> None:
    result = await run_graph(
        query=(
            "Did shipment volume or cost per shipment drive the Southeast "
            "variance in August?"
        ),
        user_id="demo-finance-user",
    )

    assert result["status"] == "access_denied"
    assert "selected_skill_instructions" not in result
    assert "validate_query" not in result["tool_trajectory"]


@pytest.mark.anyio
async def test_unsupported_question_clarifies_without_tools() -> None:
    result = await run_graph(
        query="Forecast next year's Northeast revenue.",
        user_id="demo-analyst",
    )

    assert result["status"] == "clarification_required"
    assert result["tool_trajectory"] == []
    assert result["final_answer"]