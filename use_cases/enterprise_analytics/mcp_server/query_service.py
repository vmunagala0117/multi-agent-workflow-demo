from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import compare_digest
from typing import Any

from use_cases.enterprise_analytics.golden_result_validation import (
    validate_against_golden_contract,
)
from use_cases.enterprise_analytics.mcp_server.authorization import (
    require_domains,
)
from use_cases.enterprise_analytics.mcp_server.models import (
    AnalyticsToolResult,
    QueryValidationReceipt,
    ResultValidation,
)
from use_cases.enterprise_analytics.query_policy import (
    POLICY_VERSION,
    enforce_query_policy,
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
    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        receipt_ttl: timedelta = timedelta(minutes=5),
    ) -> None:
        self._catalog = load_semantic_catalog()
        self._approved: dict[str, QueryValidationReceipt] = {}
        self._clock = clock or (lambda: datetime.now(UTC))
        self._receipt_ttl = receipt_ttl

    @staticmethod
    def _required_domains(
        plan: AnalyticsQueryPlan,
    ) -> set[AnalyticsDomain]:
        required_domains = {plan.domain}

        # Operations-driver analysis reconciles operational effects against
        # finance variance, so access to both domains is required.
        if plan.question_class == QuestionClass.OPERATIONS_DRIVER:
            required_domains.add(AnalyticsDomain.FINANCE)

        return required_domains

    @staticmethod
    def _plan_hash(plan: AnalyticsQueryPlan) -> str:
        canonical_plan = plan.model_dump_json()
        return sha256(canonical_plan.encode("utf-8")).hexdigest()

    def validate(
        self,
        *,
        user_id: str,
        plan: AnalyticsQueryPlan,
    ) -> QueryValidationReceipt:
        # Authorization runs before detailed policy validation so an
        # unauthorized caller does not receive information about policies
        # governing a domain they cannot access.
        require_domains(
            user_id,
            self._required_domains(plan),
        )

        enforce_query_policy(plan)

        filter_fields = [item.field for item in plan.filters]

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
            definition = metric_definitions.get(metric_id)
            if definition is None:
                raise ValueError(
                    f"Metric {metric_id} has no governed definition"
                )

            if definition.domain != plan.domain:
                raise ValueError(
                    f"Metric {metric_id} does not belong to {plan.domain}"
                )

            unsupported_dimensions = (
                requested_dimensions - definition.allowed_dimensions
            )
            if unsupported_dimensions:
                raise ValueError(
                    f"Metric {metric_id} does not support dimensions: "
                    + ", ".join(sorted(unsupported_dimensions))
                )

        now = self._clock()
        plan_hash = self._plan_hash(plan)

        canonical_receipt = "|".join(
            [
                user_id,
                self._catalog.version,
                POLICY_VERSION,
                plan_hash,
                now.isoformat(),
            ]
        )
        validation_id = sha256(
            canonical_receipt.encode("utf-8")
        ).hexdigest()

        receipt = QueryValidationReceipt(
            validation_id=validation_id,
            approved=True,
            user_id=user_id,
            semantic_catalog_version=self._catalog.version,
            policy_version=POLICY_VERSION,
            plan_hash=plan_hash,
            issued_at=now,
            expires_at=now + self._receipt_ttl,
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

        # Re-evaluate current authorization. If the user's access was revoked
        # after validation, the unexpired receipt is no longer executable.
        require_domains(
            user_id,
            self._required_domains(receipt.plan),
        )

        if self._clock() >= receipt.expires_at:
            self._approved.pop(validation_id, None)
            raise ValueError("Unknown or expired validation_id")

        if receipt.semantic_catalog_version != self._catalog.version:
            self._approved.pop(validation_id, None)
            raise ValueError(
                "Validation receipt semantic catalog version is stale"
            )

        if receipt.policy_version != POLICY_VERSION:
            self._approved.pop(validation_id, None)
            raise ValueError(
                "Validation receipt policy version is stale"
            )

        current_plan_hash = self._plan_hash(receipt.plan)
        if not compare_digest(
            current_plan_hash,
            receipt.plan_hash,
        ):
            self._approved.pop(validation_id, None)
            raise ValueError(
                "Validation receipt plan binding is invalid"
            )

        # Defense in depth: enforce the current policy again immediately
        # before execution or result validation.
        enforce_query_policy(receipt.plan)

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
        receipt = self._receipt(
            user_id=user_id,
            validation_id=validation_id,
        )

        errors = validate_against_golden_contract(
            plan=receipt.plan,
            observed_result=observed_result,
        )

        return ResultValidation(
            validation_id=validation_id,
            valid=not errors,
            errors=errors,
        )