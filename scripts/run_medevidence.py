from pprint import pprint

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import synthesize_with_llm
from langgraph.checkpoint.memory import InMemorySaver


def main() -> None:
    checkpointer = InMemorySaver()
    graph = build_graph(synthesis_node=synthesize_with_llm, checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": "medevidence-demo-001",
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

    final_state = graph.invoke(initial_state, config=config,)
    pprint(final_state)

    snapshot = graph.get_state(config)
    print("Thread:", config["configurable"]["thread_id"])
    print("Next nodes:", snapshot.next)
    print("Release status:", snapshot.values["release_status"])
    print("Final answer:", snapshot.values["final_answer"])


if __name__ == "__main__":
    main()