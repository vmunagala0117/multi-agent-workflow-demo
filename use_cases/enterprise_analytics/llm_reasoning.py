import json
import os
from typing import Any, Protocol

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator

from use_cases.enterprise_analytics.schemas import (
    AnalyticsQueryPlan,
    QuestionClass,
)


class SemanticIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supported: bool
    question_class: QuestionClass | None = None
    period: str | None = None
    region: str | None = None
    cost_category: str | None = None
    clarification: str | None = None

    @model_validator(mode="after")
    def validate_supported_scope(self) -> "SemanticIntent":
        if self.supported and (
            self.question_class is None
            or self.period is None
            or self.region is None
        ):
            raise ValueError(
                "Supported intent requires question class, period, and region"
            )
        return self


class GroundedNarrative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)


class EnterpriseReasoner(Protocol):
    async def classify(self, user_query: str) -> SemanticIntent: ...

    async def plan(
        self,
        *,
        user_query: str,
        intent: SemanticIntent,
        skill_instructions: str,
        dataset_schema: dict[str, Any],
        metric_definitions: list[dict[str, Any]],
    ) -> AnalyticsQueryPlan: ...

    async def synthesize(
        self,
        *,
        user_query: str,
        skill_instructions: str,
        validated_result: dict[str, Any],
    ) -> GroundedNarrative: ...


class AzureEnterpriseReasoner:
    def __init__(self, model: AzureChatOpenAI) -> None:
        self._intent_model = model.with_structured_output(SemanticIntent)
        self._plan_model = model.with_structured_output(AnalyticsQueryPlan)
        self._narrative_model = model.with_structured_output(
            GroundedNarrative
        )

    @classmethod
    def from_environment(cls) -> "AzureEnterpriseReasoner":
        load_dotenv()
        deployment = (
            os.getenv("AZURE_OPENAI_DEPLOYMENT")
            or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        )
        required = {
            "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
            "AZURE_OPENAI_API_VERSION": os.getenv(
                "AZURE_OPENAI_API_VERSION"
            ),
            "AZURE_OPENAI_DEPLOYMENT": deployment,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Missing Azure OpenAI configuration: "
                + ", ".join(missing)
            )

        model = AzureChatOpenAI(
            azure_endpoint=required["AZURE_OPENAI_ENDPOINT"],
            api_key=required["AZURE_OPENAI_API_KEY"],
            api_version=required["AZURE_OPENAI_API_VERSION"],
            azure_deployment=required["AZURE_OPENAI_DEPLOYMENT"],
            max_retries=2,
        )
        return cls(model)

    async def classify(self, user_query: str) -> SemanticIntent:
        result = await self._intent_model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "Classify a governed enterprise analytics request. "
                        "Supported question classes are finance_variance, "
                        "business_unit_contribution, and operations_driver. "
                        "Extract period as YYYY-MM and the explicitly requested "
                        "region. Use logistics_expense only when the request is "
                        "about logistics expense. Unsupported or ambiguous "
                        "requests must set supported=false and ask one concise "
                        "clarifying question. Never make authorization decisions."
                    )
                ),
                HumanMessage(content=user_query),
            ]
        )
        return SemanticIntent.model_validate(result)

    async def plan(
        self,
        *,
        user_query: str,
        intent: SemanticIntent,
        skill_instructions: str,
        dataset_schema: dict[str, Any],
        metric_definitions: list[dict[str, Any]],
    ) -> AnalyticsQueryPlan:
        context = {
            "user_query": user_query,
            "intent": intent.model_dump(mode="json"),
            "dataset_schema": dataset_schema,
            "metric_definitions": metric_definitions,
            "skill_instructions": skill_instructions,
        }
        result = await self._plan_model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "Produce only a typed analytics query plan. Preserve the "
                        "classified period, region, cost category, and question "
                        "class exactly. Use only governed metrics and dimensions. "
                        "Set row_limit to at most 100. Do not generate SQL and do "
                        "not broaden scope."
                    )
                ),
                HumanMessage(content=json.dumps(context, default=str)),
            ]
        )
        return AnalyticsQueryPlan.model_validate(result)

    async def synthesize(
        self,
        *,
        user_query: str,
        skill_instructions: str,
        validated_result: dict[str, Any],
    ) -> GroundedNarrative:
        context = {
            "user_query": user_query,
            "validated_result": validated_result,
            "skill_instructions": skill_instructions,
        }
        result = await self._narrative_model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "Explain only the supplied validated result. State money "
                        "as full dollar amounts with two decimal places and rates "
                        "as percentages with two decimal places. Do not introduce "
                        "new numbers, causes, forecasts, or recommendations."
                    )
                ),
                HumanMessage(content=json.dumps(context, default=str)),
            ]
        )
        return GroundedNarrative.model_validate(result)