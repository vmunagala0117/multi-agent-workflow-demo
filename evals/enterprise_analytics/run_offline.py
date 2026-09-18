import asyncio

from evals.enterprise_analytics.evaluators import (
    evaluate_result,
    load_cases,
)
from use_cases.enterprise_analytics.graph import (
    build_enterprise_analytics_graph,
)


async def main() -> None:
    graph = build_enterprise_analytics_graph()
    evaluations = []

    for case in load_cases():
        result = await graph.ainvoke(
            {
                "user_query": case.query,
                "user_id": case.user_id,
                "status": "received",
                "tool_trajectory": [],
            }
        )
        evaluation = evaluate_result(case, result)
        evaluations.append(evaluation)
        outcome = "PASS" if evaluation.passed else "FAIL"
        print(
            f"{outcome} {case.case_id} "
            f"score={evaluation.score:.2f}"
        )
        if not evaluation.passed:
            failed = [
                name
                for name, passed in evaluation.checks.items()
                if not passed
            ]
            print("  failed checks:", ", ".join(failed))

    passed = sum(item.passed for item in evaluations)
    total = len(evaluations)
    print(f"\nEnterpriseOps offline evaluation: {passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())