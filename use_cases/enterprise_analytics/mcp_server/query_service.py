from hashlib import sha256
from typing import Any

from use_cases.enterprise_analytics.mcp_server.authorization import (
    require_domains,
)
from use_cases.enterprise_analytics.mcp_server.models import (
    AnalyticsToolResult,
    QueryValidationReceipt,
    ResultValidation,
)
from use_cases.enterprise_analytics.reference_calculator import (
    calculate_finance_variance,
    calculate_operations_driver,
)
from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    QuestionClass,
)
from use_cases.enterprise_analytics.semantic_catalog import (
    load_semantic_catalog,
)


class QueryService:
    def __init__(self) -> None:
        self._catalog = load_semantic_catalog()
        self._approved: dict[str, QueryValidationReceipt] = {}

    def validate(
        self,
        *,
        user_id: str,
        plan: AnalyticsQueryPlan,
    ) -> QueryValidationReceipt:
        required_domains = {plan.domain}
        if plan.question_class == QuestionClass.OPERATIONS_DRIVER:
            required_domains.add(AnalyticsDomain.FINANCE)
        require_domains(user_id, required_domains)

        filter_fields = [item.field for item in plan.filters]
        if len(filter_fields) != len(set(filter_fields)):
            raise ValueError("Query plan contains duplicate filters")

        required_filters = {"period", "region"}
        if plan.domain == AnalyticsDomain.FINANCE:
            required_filters.add("cost_category")
        missing_filters = required_filters - set(filter_fields)
        if missing_filters:
            raise ValueError(
                "Query plan is missing required filters: "
                + ", ".join(sorted(missing_filters))
            )

        metric_definitions = {
            metric.metric_id: metric
            for metric in self._catalog.metrics
        }
        requested_dimensions = set(plan.dimensions) | set(filter_fields)

        for metric_id in plan.metrics:
            definition = metric_definitions[metric_id]
            if definition.domain != plan.domain:
                raise ValueError(
                    f"Metric {metric_id} does not belong to {plan.domain}"
                )
            unsupported = (
                requested_dimensions - definition.allowed_dimensions
            )
            if unsupported:
                raise ValueError(
                    f"Metric {metric_id} does not support dimensions: "
                    + ", ".join(sorted(unsupported))
                )

        canonical = "|".join(
            [
                user_id,
                self._catalog.version,
                plan.model_dump_json(),
            ]
        )
        validation_id = sha256(canonical.encode("utf-8")).hexdigest()
        receipt = QueryValidationReceipt(
            validation_id=validation_id,
            approved=True,
            user_id=user_id,
            semantic_catalog_version=self._catalog.version,
            plan=plan,
        )
        self._approved[validation_id] = receipt
        return receipt

    def _receipt(
        self,
        *,
        user_id: str,
        validation_id: str,
    ) -> QueryValidationReceipt:
        receipt = self._approved.get(validation_id)
        if receipt is None:
            raise ValueError("Unknown or expired validation_id")
        if receipt.user_id != user_id:
            raise PermissionError(
                "The validation receipt belongs to another user"
            )
        return receipt

    def execute(
        self,
        *,
        user_id: str,
        validation_id: str,
    ) -> AnalyticsToolResult:
        receipt = self._receipt(
            user_id=user_id,
            validation_id=validation_id,
        )
        filters = {
            item.field: item.value
            for item in receipt.plan.filters
        }

        if receipt.plan.question_class == QuestionClass.OPERATIONS_DRIVER:
            calculated = calculate_operations_driver(
                period=filters["period"],
                region=filters["region"],
            )
        else:
            calculated = calculate_finance_variance(
                period=filters["period"],
                region=filters["region"],
                cost_category=filters["cost_category"],
            )

        return AnalyticsToolResult(
            validation_id=validation_id,
            question_class=receipt.plan.question_class,
            data=calculated.model_dump(mode="json"),
        )

    def validate_result(
        self,
        *,
        user_id: str,
        validation_id: str,
        observed_result: dict[str, Any],
    ) -> ResultValidation:
        expected = self.execute(
            user_id=user_id,
            validation_id=validation_id,
        )
        errors = []
        if observed_result != expected.data:
            errors.append(
                "Observed result does not match the deterministic reference result"
            )

        return ResultValidation(
            validation_id=validation_id,
            valid=not errors,
            errors=errors,
        )