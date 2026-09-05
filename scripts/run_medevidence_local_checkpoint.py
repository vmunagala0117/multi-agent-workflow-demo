from pprint import pprint

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import synthesize_with_llm
from langgraph.checkpoint.memory import InMemorySaver


def main() -> None:
    checkpointer = InMemorySaver()
    graph = build_graph(synthesis_node=synthesize_with_llm, 
                        checkpointer=checkpointer,
                        interrupt_before=["synthesize"],)

    config = {
        "configurable": {
            "thread_id": "medevidence-resume-demo-001",
        }
    }

    initial_state = {
        "user_query": (
            "What evidence supports Therapy Alpha for reducing chronic "
            "pruritus in adults, and what safety limitations remain?"
        ),
        "risk_level": "low",
        "literature_results": [],
        "internal_evidence": [],
        "evidence_status": None,
        "response_mode": None,
        "synthesis": None,
        "synthesis_result": None,
        "citations": [],
        "validation_status": None,
        "errors": [],
    }

    '''
    final_state = graph.invoke(initial_state, config=config,)
    pprint(final_state)

    snapshot = graph.get_state(config)
    print("Thread:", config["configurable"]["thread_id"])
    print("Next nodes:", snapshot.next)
    print("Release status:", snapshot.values["release_status"])
    print("Final answer:", snapshot.values["final_answer"])
    '''

    paused_state = graph.invoke(initial_state, config=config)
    paused_snapshot = graph.get_state(config)

    print("--- PAUSED ---")
    print("Next nodes:", paused_snapshot.next)
    print(
        "Literature:",
        len(paused_snapshot.values["literature_results"]),
    )
    print(
        "Internal:",
        len(paused_snapshot.values["internal_evidence"]),
    )
    print("Synthesis:", paused_snapshot.values.get("synthesis"))

    # Resume the workflow from the paused state
    final_state = graph.invoke(None, config=config) #None means - continue the pending execution
    final_snapshot = graph.get_state(config)

    print("--- RESUMED ---")
    print("Next nodes:", final_snapshot.next)
    print("Release status:", final_state["release_status"])
    print("Final answer:", final_state["final_answer"])


if __name__ == "__main__":
    main()