from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.nodes import synthesize


def build_initial_state(risk_level: str) -> dict:
    return {
        "user_query": (
            "What evidence supports Therapy Alpha for reducing chronic "
            "pruritus in adults, and what safety limitations remain?"
        ),
        "risk_level": risk_level,
        "literature_results": [],
        "internal_evidence": [],
        "evidence_status": None,
        "response_mode": None,
        "synthesis_result": None,
        "synthesis": None,
        "citations": [],
        "validation_status": None,
        "final_answer": None,
        "release_status": None,
        "approval_status": None,
        "reviewer_id": None,
        "review_comment": None,
        "errors": [],
    }


def build_test_graph_and_config() -> tuple:
    graph = build_graph(
        synthesis_node=synthesize,
        checkpointer=InMemorySaver(),
    )
    config = {
        "configurable": {
            "thread_id": f"hitl-test-{uuid4()}",
        }
    }
    return graph, config


def test_low_risk_response_releases_without_review() -> None:
    graph, config = build_test_graph_and_config()

    result = graph.invoke(
        build_initial_state("low"),
        config=config,
    )

    assert "__interrupt__" not in result
    assert result["validation_status"] == "valid"
    assert result["approval_status"] is None
    assert result["release_status"] == "released"
    assert result["final_answer"] == result["synthesis"]
    assert graph.get_state(config).next == ()


def test_high_risk_response_pauses_then_approval_releases() -> None:
    graph, config = build_test_graph_and_config()

    paused = graph.invoke(
        build_initial_state("high"),
        config=config,
    )

    assert "__interrupt__" in paused
    assert len(paused["__interrupt__"]) == 1

    review_request = paused["__interrupt__"][0].value

    assert review_request["review_type"] == "high_risk_medical_evidence"
    assert review_request["risk_level"] == "high"
    assert review_request["candidate_answer"]
    assert review_request["citation_labels"]

    paused_snapshot = graph.get_state(config)

    assert paused_snapshot.next == ("human_review",)
    assert paused_snapshot.values["final_answer"] is None
    assert paused_snapshot.values["release_status"] is None

    final = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "reviewer_id": "reviewer-123",
                "comment": "Evidence and citations reviewed.",
            }
        ),
        config=config,
    )

    assert final["approval_status"] == "approved"
    assert final["reviewer_id"] == "reviewer-123"
    assert final["release_status"] == "released"
    assert final["final_answer"] == final["synthesis"]
    assert graph.get_state(config).next == ()


def test_high_risk_response_pauses_then_rejection_blocks_release() -> None:
    graph, config = build_test_graph_and_config()

    paused = graph.invoke(
        build_initial_state("high"),
        config=config,
    )

    assert "__interrupt__" in paused

    candidate = paused["synthesis"]

    final = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "reviewer_id": "reviewer-456",
                "comment": "Qualification is insufficient for release.",
            }
        ),
        config=config,
    )

    assert final["approval_status"] == "rejected"
    assert final["reviewer_id"] == "reviewer-456"
    assert final["release_status"] == "rejected"
    assert final["response_mode"] == "abstain"
    assert final["final_answer"] != candidate
    assert "not approved" in final["final_answer"].lower()
    assert graph.get_state(config).next == ()