import asyncio
from time import perf_counter
from typing import Any

from dotenv import load_dotenv
from langsmith import Client

from evals.enterprise_analytics.evaluators import (
    ExpectedOutcome,
    GoldenCase,
    evaluate_result,
)
from use_cases.enterprise_analytics.live_graph import (
    build_live_enterprise_analytics_graph,
)


DATASET_NAME = "enterpriseops-golden-v1"


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


async def _invoke_live(inputs: dict[str, Any]) -> dict[str, Any]:
    graph = build_live_enterprise_analytics_graph()
    started = perf_counter()
    result = await graph.ainvoke(
        {
            "user_query": inputs["query"],
            "user_id": inputs["user_id"],
            "status": "received",
            "tool_trajectory": [],
        }
    )
    latency_ms = round((perf_counter() - started) * 1000, 2)

    return {
        "status": result.get("status"),
        "question_class": _enum_value(
            result.get("question_class")
        ),
        "selected_skill_name": result.get("selected_skill_name"),
        "result_valid": result.get("result_valid"),
        "analytics_result": result.get("analytics_result", {}),
        "tool_trajectory": result.get("tool_trajectory", []),
        "final_answer": result.get("final_answer"),
        "claim_validation_errors": result.get(
            "claim_validation_errors", []
        ),
        "error": result.get("error"),
        "latency_ms": latency_ms,
    }


def target(inputs: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(_invoke_live(inputs))


def governed_contract_evaluator(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    reference_outputs: dict[str, Any],
) -> dict[str, Any]:
    case = GoldenCase(
        case_id=inputs["case_id"],
        query=inputs["query"],
        user_id=inputs["user_id"],
        expected=ExpectedOutcome.model_validate(
            reference_outputs["expected"]
        ),
    )
    evaluation = evaluate_result(case, outputs)
    failed_checks = [
        name
        for name, passed in evaluation.checks.items()
        if not passed
    ]
    return {
        "key": "governed_contract",
        "score": evaluation.score,
        "comment": (
            "all deterministic checks passed"
            if not failed_checks
            else "failed: " + ", ".join(failed_checks)
        ),
    }


def safe_release_evaluator(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    reference_outputs: dict[str, Any],
) -> dict[str, Any]:
    expected = reference_outputs["expected"]
    expected_status = expected["status"]
    status_matches = outputs.get("status") == expected_status

    if expected_status == "completed":
        safe = (
            status_matches
            and outputs.get("result_valid") is True
            and bool(outputs.get("final_answer"))
            and not outputs.get("claim_validation_errors")
        )
    else:
        safe = (
            status_matches
            and "validate_query"
            not in outputs.get("tool_trajectory", [])
        )

    return {
        "key": "safe_release",
        "score": int(safe),
    }


def main() -> None:
    load_dotenv()
    client = Client()
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            governed_contract_evaluator,
            safe_release_evaluator,
        ],
        experiment_prefix="enterpriseops-live-v1",
        max_concurrency=1,
    )
    print(results)


if __name__ == "__main__":
    main()