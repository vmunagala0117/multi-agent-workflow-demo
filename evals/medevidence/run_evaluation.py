import json
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "evals" / "medevidence" / "cases.jsonl"

load_dotenv(PROJECT_ROOT / ".env")

from langgraph.checkpoint.memory import InMemorySaver

from evals.medevidence.evaluators import evaluate_case
from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import (
    synthesize_with_llm,
)


def load_cases() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return [
            json.loads(line)
            for line in dataset_file
            if line.strip()
        ]


def build_initial_state(case_input: dict) -> dict:
    return {
        "user_query": case_input["user_query"],
        "risk_level": case_input["risk_level"],
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


def main() -> None:
    cases = load_cases()
    graph = build_graph(
        synthesis_node=synthesize_with_llm,
        checkpointer=InMemorySaver(),
    )

    report: list[dict] = []

    for case in cases:
        case_id = case["case_id"]
        config = {
            "configurable": {
                "thread_id": f"eval-{case_id}-{uuid4()}",
            },
            "run_name": "medevidence_evaluation_case",
            "tags": [
                "medevidence",
                "evaluation",
                case["dataset_version"],
            ],
            "metadata": {
                "case_id": case_id,
                "dataset_version": case["dataset_version"],
                "risk_level": case["input"]["risk_level"],
            },
        }

        output = graph.invoke(
            build_initial_state(case["input"]),
            config=config,
        )

        scores = evaluate_case(output, case["reference"])
        report.append(
            {
                "case_id": case_id,
                "scores": scores,
            }
        )

    print(json.dumps(report, indent=2))

    passed = sum(
        item["scores"]["overall_pass"] == 1.0
        for item in report
    )

    print(f"Passed: {passed}/{len(report)}")

    if passed != len(report):
        raise SystemExit(1)


if __name__ == "__main__":
    main()