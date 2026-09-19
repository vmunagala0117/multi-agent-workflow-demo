from functools import lru_cache
from typing import Any, Literal, Protocol
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from use_cases.enterprise_analytics.live_graph import (
    build_live_enterprise_analytics_graph,
)
from use_cases.enterprise_analytics.schemas import QuestionClass


class InvokableGraph(Protocol):
    async def ainvoke(
        self,
        input: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


class EnterpriseAnalyticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_query: str = Field(min_length=3, max_length=2000)
    user_id: str = Field(min_length=1, max_length=200)


class EnterpriseAnalyticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: Literal[
        "completed",
        "clarification_required",
        "access_denied",
    ]
    question_class: QuestionClass | None = None
    selected_skill: str | None = None
    result_valid: bool | None = None
    analytics_result: dict[str, Any] = Field(default_factory=dict)
    final_answer: str | None = None
    tool_trajectory: list[str] = Field(default_factory=list)
    error: str | None = None


@lru_cache(maxsize=1)
def get_live_graph() -> InvokableGraph:
    return build_live_enterprise_analytics_graph()


def create_enterprise_analytics_router(
    graph: InvokableGraph | None = None,
) -> APIRouter:
    router = APIRouter(
        prefix="/v1/enterprise-analytics",
        tags=["Enterprise Analytics"],
    )

    @router.post(
        "/queries",
        response_model=EnterpriseAnalyticsResponse,
    )
    async def run_query(
        request: EnterpriseAnalyticsRequest,
    ) -> EnterpriseAnalyticsResponse:
        request_id = str(uuid4())
        runtime = graph or get_live_graph()
        result = await runtime.ainvoke(
            {
                "user_query": request.user_query,
                "user_id": request.user_id,
                "status": "received",
                "tool_trajectory": [],
            },
            config={
                "tags": ["enterpriseops", "api"],
                "metadata": {
                    "request_id": request_id,
                    "user_id": request.user_id,
                },
            },
        )

        return EnterpriseAnalyticsResponse(
            request_id=request_id,
            status=result["status"],
            question_class=result.get("question_class"),
            selected_skill=result.get("selected_skill_name"),
            result_valid=result.get("result_valid"),
            analytics_result=result.get("analytics_result", {}),
            final_answer=result.get("final_answer"),
            tool_trajectory=result.get("tool_trajectory", []),
            error=result.get("error"),
        )

    return router