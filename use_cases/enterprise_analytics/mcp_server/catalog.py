from use_cases.enterprise_analytics.mcp_server.models import DatasetSchema
from use_cases.enterprise_analytics.schemas import AnalyticsDomain


DATASET_SCHEMAS: dict[AnalyticsDomain, DatasetSchema] = {
    AnalyticsDomain.FINANCE: DatasetSchema(
        domain=AnalyticsDomain.FINANCE,
        fact_sources=["finance_actuals", "finance_budget"],
        fields=[
            "period",
            "business_unit_id",
            "cost_category",
            "actual_expense",
            "budget_expense",
        ],
        dimensions={
            "period",
            "region",
            "business_unit",
            "cost_category",
        },
        relationships=[
            "finance facts join business_units on business_unit_id"
        ],
    ),
    AnalyticsDomain.OPERATIONS: DatasetSchema(
        domain=AnalyticsDomain.OPERATIONS,
        fact_sources=["operations_metrics"],
        fields=[
            "period",
            "business_unit_id",
            "actual_shipment_volume",
            "budget_shipment_volume",
            "actual_cost_per_shipment",
            "budget_cost_per_shipment",
        ],
        dimensions={"period", "region", "business_unit"},
        relationships=[
            "operations_metrics joins business_units on business_unit_id",
            "operations scope reconciles to finance scope by period and business_unit_id",
        ],
    ),
}