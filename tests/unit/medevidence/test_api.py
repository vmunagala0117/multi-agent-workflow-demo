from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from app.api.main import create_app
from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.nodes import synthesize


def client() -> TestClient:
    graph = build_graph(
        synthesis_node=synthesize,
        checkpointer=InMemorySaver(),
    )
    return TestClient(create_app(workflow_graph=graph))


def query_payload(risk_level: str) -> dict:
    return {
        "user_query": (
            "What evidence supports Therapy Alpha for reducing chronic "
            "pruritus in adults, and what safety limitations remain?"
        ),
        "risk_level": risk_level,
    }


def test_health() -> None:
    response = client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_low_risk_run_returns_released_external_response() -> None:
    response = client().post(
        "/v1/medevidence/runs",
        json=query_payload("low"),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert body["release_status"] == "released"
    assert body["final_answer"]
    assert body["citation_labels"]
    assert "literature_results" not in body
    assert "internal_evidence" not in body
    assert "errors" not in body


def test_high_risk_run_pauses_and_approval_resumes() -> None:
    test_client = client()

    paused_response = test_client.post(
        "/v1/medevidence/runs",
        json=query_payload("high"),
    )

    assert paused_response.status_code == 200
    paused = paused_response.json()
    assert paused["status"] == "review_required"
    assert paused["final_answer"] is None
    assert paused["review_request"]["candidate_answer"]

    approval_response = test_client.post(
        f"/v1/medevidence/runs/{paused['thread_id']}/review",
        json={
            "decision": "approve",
            "reviewer_id": "reviewer-123",
            "comment": "Reviewed for API test.",
        },
    )

    assert approval_response.status_code == 200
    approved = approval_response.json()
    assert approved["status"] == "completed"
    assert approved["release_status"] == "released"
    assert approved["final_answer"]


def test_completed_run_cannot_be_reviewed_again() -> None:
    test_client = client()
    completed = test_client.post(
        "/v1/medevidence/runs",
        json=query_payload("low"),
    ).json()

    response = test_client.post(
        f"/v1/medevidence/runs/{completed['thread_id']}/review",
        json={
            "decision": "approve",
            "reviewer_id": "reviewer-123",
        },
    )

    assert response.status_code == 409
