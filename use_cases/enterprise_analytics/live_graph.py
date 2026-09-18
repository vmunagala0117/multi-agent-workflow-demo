from typing import Any

from langgraph.graph import END, START, StateGraph

from use_cases.enterprise_analytics.claim_validation import (
    validate_numeric_claims,
)
from use_cases.enterprise_analytics.graph import EnterpriseOpsNodes
from use_cases.enterprise_analytics.llm_reasoning import (
    AzureEnterpriseReasoner,
    EnterpriseReasoner,
    SemanticIntent,
)
from use_cases.enterprise_analytics.mcp_gateway import LocalMCPGateway
from use_cases.enterprise_analytics.schemas import QuestionClass
from use_cases.enterprise_analytics.skill_registry import SkillRegistry
from use_cases.enterprise_analytics.state import EnterpriseAnalyticsState


class LLMEnterpriseOpsNodes(EnterpriseOpsNodes):
    def __init__(
        self,
        *,
        gateway: LocalMCPGateway,
        registry: SkillRegistry,
        reasoner: EnterpriseReasoner,
    ) -> None:
        super().__init__(gateway=gateway, registry=registry)
        self.reasoner = reasoner

    async def classify(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        decision = await self.reasoner.classify(state["user_query"])
        if not decision.supported:
            return {
                "status": "clarification_required",
                "final_answer": decision.clarification,
            }
        return {
            "status": "classified",
            "question_class": decision.question_class,
            "period": decision.period,
            "region": decision.region,
            "cost_category": decision.cost_category,
        }

    async def build_plan(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        intent = SemanticIntent(
            supported=True,
            question_class=state["question_class"],
            period=state["period"],
            region=state["region"],
            cost_category=state.get("cost_category"),
        )
        plan = await self.reasoner.plan(
            user_query=state["user_query"],
            intent=intent,
            skill_instructions=state["selected_skill_instructions"],
            dataset_schema=state["dataset_schema"],
            metric_definitions=state["metric_definitions"],
        )

        filters = {item.field: item.value for item in plan.filters}
        required_scope = {
            "period": state["period"],
            "region": state["region"],
        }
        if state["question_class"] != QuestionClass.OPERATIONS_DRIVER:
            required_scope["cost_category"] = state["cost_category"]

        if (
            plan.question_class != state["question_class"]
            or any(
                filters.get(field) != value
                for field, value in required_scope.items()
            )
        ):
            raise ValueError(
                "LLM query plan changed the classified request scope"
            )

        return {"status": "planned", "query_plan": plan}

    async def release(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        if not state["result_valid"]:
            return {
                "status": "clarification_required",
                "final_answer": None,
                "error": "; ".join(state["validation_errors"]),
            }

        narrative = await self.reasoner.synthesize(
            user_query=state["user_query"],
            skill_instructions=state["selected_skill_instructions"],
            validated_result=state["analytics_result"],
        )
        errors = validate_numeric_claims(
            answer=narrative.answer,
            result=state["analytics_result"],
            question_class=state["question_class"],
        )
        if errors:
            return {
                "status": "clarification_required",
                "final_answer": None,
                "claim_validation_errors": errors,
                "error": "; ".join(errors),
            }
        return {
            "status": "completed",
            "final_answer": narrative.answer,
            "claim_validation_errors": [],
        }


def build_live_enterprise_analytics_graph(
    reasoner: EnterpriseReasoner | None = None,
):
    nodes = LLMEnterpriseOpsNodes(
        gateway=LocalMCPGateway(),
        registry=SkillRegistry(),
        reasoner=reasoner or AzureEnterpriseReasoner.from_environment(),
    )
    graph = StateGraph(EnterpriseAnalyticsState)

    graph.add_node("classify", nodes.classify)
    graph.add_node("resolve_access", nodes.resolve_access)
    graph.add_node("load_skill", nodes.load_skill)
    graph.add_node("load_context", nodes.load_context)
    graph.add_node("build_plan", nodes.build_plan)
    graph.add_node("validate_plan", nodes.validate_plan)
    graph.add_node("execute", nodes.execute)
    graph.add_node("validate_result", nodes.validate_result)
    graph.add_node("release", nodes.release)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        lambda state: state["status"],
        {
            "classified": "resolve_access",
            "clarification_required": END,
        },
    )
    graph.add_conditional_edges(
        "resolve_access",
        lambda state: state["status"],
        {"authorized": "load_skill", "access_denied": END},
    )
    graph.add_conditional_edges(
        "load_skill",
        lambda state: state["status"],
        {"skill_loaded": "load_context", "access_denied": END},
    )
    graph.add_edge("load_context", "build_plan")
    graph.add_edge("build_plan", "validate_plan")
    graph.add_edge("validate_plan", "execute")
    graph.add_edge("execute", "validate_result")
    graph.add_edge("validate_result", "release")
    graph.add_edge("release", END)
    return graph.compile()