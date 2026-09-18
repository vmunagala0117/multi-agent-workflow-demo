import asyncio
import json

from dotenv import load_dotenv

from use_cases.enterprise_analytics.live_graph import (
    build_live_enterprise_analytics_graph,
)


async def main() -> None:
    load_dotenv()
    graph = build_live_enterprise_analytics_graph()
    result = await graph.ainvoke(
        {
            "user_query": (
                "Could you break down how Southeast logistics spending "
                "performed against plan for August 2026 and explain the gap?"
            ),
            "user_id": "demo-finance-user",
            "status": "received",
            "tool_trajectory": [],
        }
    )

    summary = {
        "status": result.get("status"),
        "question_class": result.get("question_class"),
        "selected_skill": result.get("selected_skill_name"),
        "result_valid": result.get("result_valid"),
        "claim_validation_errors": result.get(
            "claim_validation_errors",
            [],
        ),
        "tool_trajectory": result.get("tool_trajectory", []),
        "final_answer": result.get("final_answer"),
        "error": result.get("error"),
    }
    print(json.dumps(summary, indent=2, default=str))

    if result.get("status") != "completed":
        raise SystemExit("Live EnterpriseOps smoke test did not complete")


if __name__ == "__main__":
    asyncio.run(main())