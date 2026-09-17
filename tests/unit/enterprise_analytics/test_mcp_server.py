import pytest
from mcp import Client

from use_cases.enterprise_analytics.mcp_server.server import mcp


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as connected:
        yield connected


@pytest.mark.anyio
async def test_lists_authorized_domains(client: Client) -> None:
    result = await client.call_tool(
        "list_available_domains",
        {"user_id": "demo-analyst"},
    )

    assert result.is_error is False
    assert result.structured_content["domains"] == [
        "finance",
        "operations",
    ]


@pytest.mark.anyio
async def test_returns_structured_metric_definition(client: Client) -> None:
    result = await client.call_tool(
        "get_metric_definition",
        {
            "user_id": "demo-finance-user",
            "metric_id": "variance_amount",
        },
    )

    assert result.is_error is False
    assert result.structured_content["formula"] == (
        "actual_expense - budget_expense"
    )


@pytest.mark.anyio
async def test_validates_executes_and_checks_a_finance_plan(
    client: Client,
) -> None:
    plan = {
        "domain": "finance",
        "question_class": "finance_variance",
        "metrics": [
            "actual_expense",
            "budget_expense",
            "variance_amount",
            "variance_percent",
        ],
        "dimensions": ["region"],
        "filters": [
            {"field": "period", "value": "2026-08"},
            {"field": "region", "value": "Southeast"},
            {
                "field": "cost_category",
                "value": "logistics_expense",
            },
        ],
        "row_limit": 100,
    }

    validation = await client.call_tool(
        "validate_query",
        {"user_id": "demo-finance-user", "plan": plan},
    )
    assert validation.is_error is False
    validation_id = validation.structured_content["validation_id"]

    execution = await client.call_tool(
        "execute_analytics_query",
        {
            "user_id": "demo-finance-user",
            "validation_id": validation_id,
        },
    )
    assert execution.is_error is False
    assert execution.structured_content["data"]["variance_amount"] == (
        "150000.00"
    )

    checked = await client.call_tool(
        "validate_result",
        {
            "user_id": "demo-finance-user",
            "validation_id": validation_id,
            "observed_result": execution.structured_content["data"],
        },
    )
    assert checked.is_error is False
    assert checked.structured_content["valid"] is True


@pytest.mark.anyio
async def test_unauthorized_metric_request_is_a_tool_error(
    client: Client,
) -> None:
    result = await client.call_tool(
        "get_metric_definition",
        {
            "user_id": "demo-finance-user",
            "metric_id": "rate_effect",
        },
    )

    assert result.is_error is True
    assert "not authorized" in result.content[0].text


@pytest.mark.anyio
async def test_execution_requires_a_validation_receipt(
    client: Client,
) -> None:
    result = await client.call_tool(
        "execute_analytics_query",
        {
            "user_id": "demo-finance-user",
            "validation_id": "not-a-valid-receipt",
        },
    )

    assert result.is_error is True
    assert "Unknown or expired" in result.content[0].text