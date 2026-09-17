from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from use_cases.enterprise_analytics.mcp_server.authorization import (
    get_allowed_domains,
    require_domains,
)
from use_cases.enterprise_analytics.mcp_server.catalog import (
    DATASET_SCHEMAS,
)
from use_cases.enterprise_analytics.mcp_server.models import (
    AnalyticsToolResult,
    AvailableDomains,
    DatasetSchema,
    QueryValidationReceipt,
    ResultValidation,
)
from use_cases.enterprise_analytics.mcp_server.query_service import (
    QueryService,
)
from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    AnalyticsQueryPlan,
    MetricDefinition,
    MetricName,
)
from use_cases.enterprise_analytics.semantic_catalog import (
    load_semantic_catalog,
)


mcp = MCPServer("EnterpriseOps")
query_service = QueryService()
semantic_catalog = load_semantic_catalog()
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=False,
)


@mcp.tool(annotations=READ_ONLY)
def list_available_domains(user_id: str) -> AvailableDomains:
    """List the analytics domains available to the demo identity."""
    return AvailableDomains(
        user_id=user_id,
        domains=sorted(
            get_allowed_domains(user_id),
            key=lambda domain: domain.value,
        ),
    )


@mcp.tool(annotations=READ_ONLY)
def get_metric_definition(
    user_id: str,
    metric_id: MetricName,
) -> MetricDefinition:
    """Return an authorized governed definition for one metric."""
    definition = next(
        (
            metric
            for metric in semantic_catalog.metrics
            if metric.metric_id == metric_id
        ),
        None,
    )
    if definition is None:
        raise ToolError(f"Unknown metric: {metric_id}")

    try:
        require_domains(user_id, {definition.domain})
    except PermissionError as exc:
        raise ToolError(str(exc)) from exc
    return definition


@mcp.tool(annotations=READ_ONLY)
def get_dataset_schema(
    user_id: str,
    domain: AnalyticsDomain,
) -> DatasetSchema:
    """Return the authorized dataset contract for one domain."""
    try:
        require_domains(user_id, {domain})
    except PermissionError as exc:
        raise ToolError(str(exc)) from exc
    return DATASET_SCHEMAS[domain]


@mcp.tool(annotations=READ_ONLY)
def validate_query(
    user_id: str,
    plan: AnalyticsQueryPlan,
) -> QueryValidationReceipt:
    """Validate and bind a structured query plan before execution."""
    try:
        return query_service.validate(user_id=user_id, plan=plan)
    except (PermissionError, ValueError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(annotations=READ_ONLY)
def execute_analytics_query(
    user_id: str,
    validation_id: str,
) -> AnalyticsToolResult:
    """Execute a previously validated analytics plan."""
    try:
        return query_service.execute(
            user_id=user_id,
            validation_id=validation_id,
        )
    except (PermissionError, ValueError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(annotations=READ_ONLY)
def validate_result(
    user_id: str,
    validation_id: str,
    observed_result: dict[str, Any],
) -> ResultValidation:
    """Validate an observed analytics result against the reference oracle."""
    try:
        return query_service.validate_result(
            user_id=user_id,
            validation_id=validation_id,
            observed_result=observed_result,
        )
    except (PermissionError, ValueError) as exc:
        raise ToolError(str(exc)) from exc


if __name__ == "__main__":
    mcp.run()