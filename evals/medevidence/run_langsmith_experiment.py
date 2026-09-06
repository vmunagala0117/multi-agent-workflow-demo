from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from evals.medevidence.workflow_groundedness import (
    evaluate_workflow_groundedness,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_NAME = "medevidence-golden-v1"

load_dotenv(PROJECT_ROOT / ".env")

from langgraph.checkpoint.memory import InMemorySaver
from langsmith import Client

from evals.medevidence.evaluators import evaluate_case
from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import (
    synthesize_with_llm,
)


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())

    if isinstance(value, dict):
        return {
            key: to_jsonable(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [to_jsonable(item) for item in value]

    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]

    return value


def build_initial_state(inputs: dict) -> dict:
    return {
        "user_query": inputs["user_query"],
        "risk_level": inputs["risk_level"],
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


checkpointer = InMemorySaver()
graph = build_graph(
    synthesis_node=synthesize_with_llm,
    checkpointer=checkpointer,
)


def target(inputs: dict) -> dict:
    config = {
        "configurable": {
            "thread_id": f"langsmith-eval-{uuid4()}",
        },
        "run_name": "medevidence_graph",
        "tags": ["medevidence", "managed-experiment"],
        "metadata": {
            "workflow_version": "phase-5-v1",
            "risk_level": inputs["risk_level"],
        },
    }

    output = graph.invoke(
        build_initial_state(inputs),
        config=config,
    )

    evaluation_output = {
        "release_status": output.get("release_status"),
        "response_mode": output.get("response_mode"),
        "validation_status": output.get("validation_status"),
        "synthesis_result": output.get("synthesis_result"),
        "literature_results": output.get("literature_results", []),
        "internal_evidence": output.get("internal_evidence", []),
        "final_answer": output.get("final_answer"),
    }

    return to_jsonable(evaluation_output)


def deterministic_evaluator(
    outputs: dict,
    reference_outputs: dict,
) -> list[dict]:
    scores = evaluate_case(outputs, reference_outputs)

    return [
        {
            "key": key,
            "score": score,
        }
        for key, score in scores.items()
    ]


def groundedness_evaluator(
    inputs: dict,
    outputs: dict,
) -> list[dict]:
    return evaluate_workflow_groundedness(inputs, outputs)

def main() -> None:
    client = Client()

    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[deterministic_evaluator, groundedness_evaluator,],
        experiment_prefix="medevidence-azure-groundedness",
        description=(
            "Azure-backed MedEvidence experiment with deterministic "
            "controls and calibrated claim-level groundedness scoring."
        ),
        max_concurrency=1,
        metadata={
            "workflow_version": "phase-5-v1",
            "dataset_version": "v1",
            "synthesis_backend": "azure-openai",
            "deterministic_evaluator_version": "v1",
            "groundedness_evaluator_version": "v1",
        },
    )

    print(results)


if __name__ == "__main__":
    main()