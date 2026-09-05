import os
from pathlib import Path
from pprint import pprint
from uuid import uuid4

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from langgraph.checkpoint.memory import InMemorySaver

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import (
    synthesize_with_llm,
)


def main() -> None:
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
        "final_answer": None,
        "release_status": None,
        "approval_status": None,
        "reviewer_id": None,
        "review_comment": None,
        "errors": [],
    }

    # Use a new thread for each independent execution.
    thread_id = f"medevidence-observability-{uuid4()}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "run_name": "medevidence_research_workflow",
        "tags": [
            "medevidence",
            "local-demo",
            "phase-5",
        ],
        "metadata": {
            "use_case": "medevidence_research",
            "environment": "local",
            "workflow_version": "phase-5-v1",
            "risk_level": initial_state["risk_level"],
        },
    }

    # Native LangSmith tracing is automatically enabled through
    # the LANGSMITH_* environment variables.
    print(
        "LangSmith tracing:",
        os.getenv("LANGSMITH_TRACING", "false"),
    )
    print(
        "LangSmith project:",
        os.getenv("LANGSMITH_PROJECT", "default"),
    )

    checkpointer = InMemorySaver()

    graph = build_graph(
        synthesis_node=synthesize_with_llm,
        checkpointer=checkpointer,
    )

    final_state = graph.invoke(
        initial_state,
        config=config,
    )

    pprint(final_state)

    snapshot = graph.get_state(config)

    print("Thread:", thread_id)
    print("Next nodes:", snapshot.next)
    print("Release status:", final_state["release_status"])
    print("Final answer:", final_state["final_answer"])


if __name__ == "__main__":
    main()