from decimal import Decimal
from typing import Any

from langgraph.graph import END, START, StateGraph

from use_cases.enterprise_analytics.mcp_gateway import LocalMCPGateway
from use_cases.enterprise_analytics.routing import classify_intent
from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    FilterCondition,
    MetricName,
    QuestionClass,
)
from use_cases.enterprise_analytics.skill_registry import (
    SkillRegistry,
    SkillRegistryError,
)
from use_cases.enterprise_analytics.state import EnterpriseAnalyticsState


class EnterpriseOpsNodes:
    def __init__(
        self,
        *,
        gateway: LocalMCPGateway,
        registry: SkillRegistry,
    ) -> None:
        self.gateway = gateway
        self.registry = registry

    def classify(self, state: EnterpriseAnalyticsState) -> dict[str, Any]:
        decision = classify_intent(state["user_query"])
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

    async def resolve_access(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        payload = await self.gateway.call(
            "list_available_domains",
            {"user_id": state["user_id"]},
        )
        domains = {
            AnalyticsDomain(value) for value in payload["domains"]
        }
        if not domains:
            return {
                "status": "access_denied",
                "error": "No authorized analytics domains",
                "final_answer": (
                    "You are not authorized for the requested analytics domain."
                ),
                "tool_trajectory": ["list_available_domains"],
            }
        return {
            "status": "authorized",
            "allowed_domains": domains,
            "tool_trajectory": ["list_available_domains"],
        }

    def load_skill(self, state: EnterpriseAnalyticsState) -> dict[str, Any]:
        try:
            selected = self.registry.select(
                question_class=state["question_class"],
                allowed_domains=state["allowed_domains"],
            )
        except SkillRegistryError as exc:
            return {
                "status": "access_denied",
                "error": str(exc),
                "final_answer": (
                    "You are not authorized for the requested analytics domain."
                ),
            }

        return {
            "status": "skill_loaded",
            "selected_skill_name": selected.metadata.name,
            "selected_skill_version": selected.metadata.version,
            "selected_skill_instructions": selected.instructions,
            "allowed_tools": selected.metadata.allowed_tools,
        }

    def _require_tool(
        self,
        state: EnterpriseAnalyticsState,
        tool_name: str,
    ) -> None:
        if tool_name not in state["allowed_tools"]:
            raise PermissionError(
                f"Selected skill does not allow tool {tool_name}"
            )

    async def load_context(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        self._require_tool(state, "get_dataset_schema")
        schema = await self.gateway.call(
            "get_dataset_schema",
            {
                "user_id": state["user_id"],
                "domain": self._plan_domain(state).value,
            },
        )

        self._require_tool(state, "get_metric_definition")
        selected = self.registry.select(
            question_class=state["question_class"],
            allowed_domains=state["allowed_domains"],
        )
        definitions = []
        trajectory = ["get_dataset_schema"]
        for metric in sorted(
            selected.metadata.required_metrics,
            key=lambda item: item.value,
        ):
            definitions.append(
                await self.gateway.call(
                    "get_metric_definition",
                    {
                        "user_id": state["user_id"],
                        "metric_id": metric.value,
                    },
                )
            )
            trajectory.append(f"get_metric_definition:{metric.value}")

        return {
            "status": "context_loaded",
            "dataset_schema": schema,
            "metric_definitions": definitions,
            "tool_trajectory": trajectory,
        }

    def _plan_domain(
        self,
        state: EnterpriseAnalyticsState,
    ) -> AnalyticsDomain:
        if state["question_class"] == QuestionClass.OPERATIONS_DRIVER:
            return AnalyticsDomain.OPERATIONS
        return AnalyticsDomain.FINANCE

    def build_plan(self, state: EnterpriseAnalyticsState) -> dict[str, Any]:
        question_class = state["question_class"]
        filters = [
            FilterCondition(field="period", value=state["period"]),
            FilterCondition(field="region", value=state["region"]),
        ]

        if question_class == QuestionClass.OPERATIONS_DRIVER:
            metrics = [
                MetricName.ACTUAL_SHIPMENT_VOLUME,
                MetricName.BUDGET_SHIPMENT_VOLUME,
                MetricName.ACTUAL_COST_PER_SHIPMENT,
                MetricName.BUDGET_COST_PER_SHIPMENT,
                MetricName.VOLUME_EFFECT,
                MetricName.RATE_EFFECT,
            ]
            dimensions = ["business_unit"]
        else:
            metrics = [
                MetricName.ACTUAL_EXPENSE,
                MetricName.BUDGET_EXPENSE,
                MetricName.VARIANCE_AMOUNT,
                MetricName.VARIANCE_PERCENT,
            ]
            dimensions = (
                ["business_unit"]
                if question_class
                == QuestionClass.BUSINESS_UNIT_CONTRIBUTION
                else []
            )
            filters.append(
                FilterCondition(
                    field="cost_category",
                    value=state["cost_category"],
                )
            )

        return {
            "status": "planned",
            "query_plan": AnalyticsQueryPlan(
                domain=self._plan_domain(state),
                question_class=question_class,
                metrics=metrics,
                dimensions=dimensions,
                filters=filters,
                row_limit=100,
            ),
        }

    async def validate_plan(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        self._require_tool(state, "validate_query")
        receipt = await self.gateway.call(
            "validate_query",
            {
                "user_id": state["user_id"],
                "plan": state["query_plan"].model_dump(mode="json"),
            },
        )
        return {
            "status": "plan_validated",
            "validation_id": receipt["validation_id"],
            "tool_trajectory": ["validate_query"],
        }

    async def execute(self, state: EnterpriseAnalyticsState) -> dict[str, Any]:
        self._require_tool(state, "execute_analytics_query")
        result = await self.gateway.call(
            "execute_analytics_query",
            {
                "user_id": state["user_id"],
                "validation_id": state["validation_id"],
            },
        )
        return {
            "status": "executed",
            "analytics_result": result["data"],
            "tool_trajectory": ["execute_analytics_query"],
        }

    async def validate_result(
        self,
        state: EnterpriseAnalyticsState,
    ) -> dict[str, Any]:
        self._require_tool(state, "validate_result")
        validation = await self.gateway.call(
            "validate_result",
            {
                "user_id": state["user_id"],
                "validation_id": state["validation_id"],
                "observed_result": state["analytics_result"],
            },
        )
        return {
            "status": "result_validated",
            "result_valid": validation["valid"],
            "validation_errors": validation["errors"],
            "tool_trajectory": ["validate_result"],
        }

    def release(self, state: EnterpriseAnalyticsState) -> dict[str, Any]:
        if not state["result_valid"]:
            return {
                "status": "clarification_required",
                "final_answer": None,
                "error": "; ".join(state["validation_errors"]),
            }

        data = state["analytics_result"]
        if state["question_class"] == QuestionClass.OPERATIONS_DRIVER:
            answer = (
                f"For {data['region']} in {data['period']}, the validated "
                f"expense variance was ${Decimal(data['total_variance']):,.2f}. "
                f"Shipment volume contributed "
                f"${Decimal(data['volume_effect']):,.2f}, while cost per "
                f"shipment contributed ${Decimal(data['rate_effect']):,.2f}. "
                f"The primary driver was {data['primary_driver']}."
            )
        else:
            direction = (
                "unfavorable"
                if Decimal(data["variance_amount"]) > 0
                else "favorable"
            )
            answer = (
                f"For {data['region']} in {data['period']}, actual logistics "
                f"expense was ${Decimal(data['actual_expense']):,.2f} versus "
                f"a budget of ${Decimal(data['budget_expense']):,.2f}, a "
                f"${Decimal(data['variance_amount']):,.2f} {direction} "
                f"variance ({Decimal(data['variance_percent']):,.2f}%)."
            )
            if (
                state["question_class"]
                == QuestionClass.BUSINESS_UNIT_CONTRIBUTION
            ):
                top = data["contributions"][0]
                answer += (
                    f" {top['business_unit_name']} was the largest contributor "
                    f"at ${Decimal(top['variance_amount']):,.2f}."
                )

        return {
            "status": "completed",
            "final_answer": answer,
        }


def build_enterprise_analytics_graph():
    nodes = EnterpriseOpsNodes(
        gateway=LocalMCPGateway(),
        registry=SkillRegistry(),
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
        {
            "authorized": "load_skill",
            "access_denied": END,
        },
    )
    graph.add_conditional_edges(
        "load_skill",
        lambda state: state["status"],
        {
            "skill_loaded": "load_context",
            "access_denied": END,
        },
    )
    graph.add_edge("load_context", "build_plan")
    graph.add_edge("build_plan", "validate_plan")
    graph.add_edge("validate_plan", "execute")
    graph.add_edge("execute", "validate_result")
    graph.add_edge("validate_result", "release")
    graph.add_edge("release", END)

    return graph.compile()