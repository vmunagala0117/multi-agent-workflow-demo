import argparse
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import synthesize_with_llm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = (
    PROJECT_ROOT / ".local" / "medevidence_checkpoints.sqlite"
)


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("pause", "resume"))
    parser.add_argument("--thread-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "configurable": {
            "thread_id": args.thread_id,
        }
    }

    with SqliteSaver.from_conn_string(
        str(CHECKPOINT_PATH)
    ) as checkpointer:
        graph = build_graph(
            synthesis_node=synthesize_with_llm,
            checkpointer=checkpointer,
            interrupt_before=["synthesize"],
        )

        if args.action == "pause":
            graph.invoke(
                build_initial_state(),
                config=config,
            )

            snapshot = graph.get_state(config)
            print("Execution paused.")
            print("Thread ID:", args.thread_id)
            print("Next nodes:", snapshot.next)
            print(
                "Literature results:",
                len(snapshot.values["literature_results"]),
            )
            print(
                "Internal evidence:",
                len(snapshot.values["internal_evidence"]),
            )
            print("Checkpoint file:", CHECKPOINT_PATH)
            return

        snapshot = graph.get_state(config)
        if snapshot.next != ("synthesize",):
            raise RuntimeError(
                "The requested thread is not paused before synthesis. "
                f"Pending nodes: {snapshot.next}"
            )

        final_state = graph.invoke(None, config=config)
        final_snapshot = graph.get_state(config)

        print("Execution resumed in a new process.")
        print("Thread ID:", args.thread_id)
        print("Next nodes:", final_snapshot.next)
        print("Release status:", final_state["release_status"])
        print("Final answer:", final_state["final_answer"])


if __name__ == "__main__":
    main()