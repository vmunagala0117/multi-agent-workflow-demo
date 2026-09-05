from langgraph.checkpoint.memory import InMemorySaver

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.nodes import synthesize


def build_initial_state() -> dict:
    return {
        "user_query": (
            "What evidence supports Therapy Alpha for reducing chronic "
            "pruritus in adults, and what safety limitations remain?"
        ),
        "risk_level": "low",
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
        "errors": [],
    }


def test_graph_pauses_before_synthesis_and_resumes_once() -> None:
    synthesis_inputs: list[tuple[int, int]] = []

    def synthesis_spy(state: dict) -> dict:
        synthesis_inputs.append(
            (
                len(state["literature_results"]),
                len(state["internal_evidence"]),
            )
        )
        return synthesize(state)

    checkpointer = InMemorySaver()
    graph = build_graph(
        synthesis_node=synthesis_spy,
        checkpointer=checkpointer,
        interrupt_before=["synthesize"],
    )
    config = {
        "configurable": {
            "thread_id": "checkpoint-resume-unit-test",
        }
    }

    paused_state = graph.invoke(
        build_initial_state(),
        config=config,
    )
    paused_snapshot = graph.get_state(config)

    assert paused_snapshot.next == ("synthesize",)
    assert synthesis_inputs == []
    assert len(paused_snapshot.values["literature_results"]) > 0
    assert len(paused_snapshot.values["internal_evidence"]) > 0
    assert paused_snapshot.values["synthesis"] is None

    final_state = graph.invoke(None, config=config)
    final_snapshot = graph.get_state(config)

    assert len(synthesis_inputs) == 1
    assert synthesis_inputs[0][0] > 0
    assert synthesis_inputs[0][1] > 0
    assert final_snapshot.next == ()
    assert final_state["validation_status"] == "valid"
    assert final_state["release_status"] == "released"
    assert final_state["final_answer"]