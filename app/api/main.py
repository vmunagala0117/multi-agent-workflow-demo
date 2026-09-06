from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import (
    synthesize_with_llm,
)


RiskLevel = Literal["low", "medium", "high"]
RunStatus = Literal["completed", "review_required"]


class ResearchRequest(BaseModel):
    user_query: str = Field(min_length=1, max_length=4000)
    risk_level: RiskLevel = "low"


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reviewer_id: str = Field(min_length=1, max_length=200)
    comment: str | None = Field(default=None, max_length=2000)


class RunResponse(BaseModel):
    thread_id: str
    status: RunStatus
    release_status: str | None = None
    response_mode: str | None = None
    final_answer: str | None = None
    citation_labels: list[str] = Field(default_factory=list)
    review_request: dict | None = None


def build_initial_state(request: ResearchRequest) -> dict:
    return {
        "user_query": request.user_query,
        "risk_level": request.risk_level,
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


def graph_config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "run_name": "medevidence_api_workflow",
        "tags": ["medevidence", "api"],
        "metadata": {
            "thread_id": thread_id,
            "workflow_version": "phase-6-v1",
        },
    }


def citation_labels(values: dict) -> list[str]:
    return [
        record["citation_label"]
        for record in values.get("citations", [])
    ]


def external_response(
    *,
    thread_id: str,
    values: dict,
    review_request: dict | None = None,
) -> RunResponse:
    return RunResponse(
        thread_id=thread_id,
        status=(
            "review_required"
            if review_request is not None
            else "completed"
        ),
        release_status=values.get("release_status"),
        response_mode=values.get("response_mode"),
        final_answer=values.get("final_answer"),
        citation_labels=citation_labels(values),
        review_request=review_request,
    )


def create_app(workflow_graph=None) -> FastAPI:
    graph = workflow_graph or build_graph(
        synthesis_node=synthesize_with_llm,
        checkpointer=InMemorySaver(),
    )

    api = FastAPI(
        title="MedEvidence API",
        version="1.0.0",
        description=(
            "Synthetic medical-evidence workflow demonstration. "
            "Not for clinical use."
        ),
    )

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post(
        "/v1/medevidence/runs",
        response_model=RunResponse,
    )
    def start_run(request: ResearchRequest) -> RunResponse:
        thread_id = str(uuid4())
        result = graph.invoke(
            build_initial_state(request),
            config=graph_config(thread_id),
        )

        interrupts = result.get("__interrupt__", ())
        review_payload = (
            interrupts[0].value
            if interrupts
            else None
        )

        return external_response(
            thread_id=thread_id,
            values=result,
            review_request=review_payload,
        )

    @api.get(
        "/v1/medevidence/runs/{thread_id}",
        response_model=RunResponse,
    )
    def get_run(thread_id: str) -> RunResponse:
        snapshot = graph.get_state(graph_config(thread_id))
        if not snapshot.values:
            raise HTTPException(
                status_code=404,
                detail="Workflow thread was not found.",
            )

        status: RunStatus = (
            "review_required"
            if snapshot.next == ("human_review",)
            else "completed"
        )

        return RunResponse(
            thread_id=thread_id,
            status=status,
            release_status=snapshot.values.get("release_status"),
            response_mode=snapshot.values.get("response_mode"),
            final_answer=snapshot.values.get("final_answer"),
            citation_labels=citation_labels(snapshot.values),
        )

    @api.post(
        "/v1/medevidence/runs/{thread_id}/review",
        response_model=RunResponse,
    )
    def review_run(
        thread_id: str,
        request: ReviewRequest,
    ) -> RunResponse:
        config = graph_config(thread_id)
        snapshot = graph.get_state(config)

        if not snapshot.values:
            raise HTTPException(
                status_code=404,
                detail="Workflow thread was not found.",
            )

        if snapshot.next != ("human_review",):
            raise HTTPException(
                status_code=409,
                detail="Workflow is not awaiting human review.",
            )

        result = graph.invoke(
            Command(
                resume={
                    "decision": request.decision,
                    "reviewer_id": request.reviewer_id,
                    "comment": request.comment,
                }
            ),
            config=config,
        )

        return external_response(
            thread_id=thread_id,
            values=result,
        )

    return api


app = create_app()
