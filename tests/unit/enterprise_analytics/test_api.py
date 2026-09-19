from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.enterprise_analytics import (
    create_enterprise_analytics_router,
)


class FakeGraph:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.last_input: dict[str, Any] | None = None
        self.last_config: dict[str, Any] | None = None

    async def ainvoke(
        self,
        input: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.last_input = input
        self.last_config = config
        return self.result


def client_for(result: dict[str, Any]) -> tuple[TestClient, FakeGraph]:
    graph = FakeGraph(result)
    app = FastAPI()
    app.include_router(create_enterprise_analytics_router(graph=graph))
    return TestClient(app), graph


def test_completed_query_projects_governed_response() -> None:
    client, graph = client_for(
        {
            "status": "completed",
            "question_class": "finance_variance",
            "selected_skill_name": "finance_variance",
            "result_valid": True,
            "analytics_result": {
                "variance_amount": "150000.00",
            },
            "final_answer": (
                "Southeast logistics expense was $150,000.00 "
                "over budget."
            ),
            "tool_trajectory": [
                "validate_query",
                "execute_analytics_query",
                "validate_result",
            ],
        }
    )

    response = client.post(
        "/v1/enterprise-analytics/queries",
        json={
            "user_query": (
                "Why did Southeast logistics expense exceed budget "
                "in August?"
            ),
            "user_id": "demo-finance-user",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["selected_skill"] == "finance_variance"
    assert body["result_valid"] is True
    assert body["analytics_result"]["variance_amount"] == "150000.00"
    assert body["request_id"]
    assert graph.last_input["user_id"] == "demo-finance-user"
    assert graph.last_config["metadata"]["request_id"] == body["request_id"]


def test_clarification_does_not_expose_internal_result() -> None:
    client, _ = client_for(
        {
            "status": "clarification_required",
            "final_answer": "Please provide the reporting period.",
            "tool_trajectory": [],
        }
    )

    response = client.post(
        "/v1/enterprise-analytics/queries",
        json={
            "user_query": "Why did Southeast expense exceed budget?",
            "user_id": "demo-finance-user",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "clarification_required"
    assert body["analytics_result"] == {}
    assert body["tool_trajectory"] == []


def test_access_denied_stops_before_query_validation() -> None:
    client, _ = client_for(
        {
            "status": "access_denied",
            "final_answer": None,
            "error": "User is not authorized for required domains",
            "tool_trajectory": ["list_available_domains"],
        }
    )

    response = client.post(
        "/v1/enterprise-analytics/queries",
        json={
            "user_query": (
                "Did shipment volume or cost per shipment drive the "
                "Southeast variance in August?"
            ),
            "user_id": "demo-finance-user",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "access_denied"
    assert "validate_query" not in body["tool_trajectory"]
    assert body["final_answer"] is None