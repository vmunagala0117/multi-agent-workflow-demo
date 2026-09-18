import pytest

from evals.enterprise_analytics.evaluators import (
    evaluate_result,
    load_cases,
)
from use_cases.enterprise_analytics.graph import (
    build_enterprise_analytics_graph,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_dataset_has_required_coverage() -> None:
    cases = load_cases()
    case_ids = {case.case_id for case in cases}

    assert len(cases) == 6
    assert {
        "finance-variance-001",
        "business-unit-001",
        "operations-driver-001",
        "authorization-denied-001",
        "unsupported-scope-001",
        "missing-period-001",
    } == case_ids


@pytest.mark.anyio
async def test_all_offline_golden_cases_pass() -> None:
    graph = build_enterprise_analytics_graph()

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
        assert evaluation.passed, (
            case.case_id,
            evaluation.checks,
        )