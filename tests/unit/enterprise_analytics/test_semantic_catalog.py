import json

import pytest
from pydantic import ValidationError

from use_cases.enterprise_analytics.schemas import (
    AggregationRule,
    MetricName,
    SemanticCatalog,
)
from use_cases.enterprise_analytics.semantic_catalog import (
    DEFAULT_CATALOG_PATH,
    load_semantic_catalog,
)


def test_catalog_loads_and_contains_all_governed_metrics() -> None:
    catalog = load_semantic_catalog()

    assert catalog.version == "1.0.0"
    assert {metric.metric_id for metric in catalog.metrics} == set(MetricName)


def test_variance_direction_and_formula_are_explicit() -> None:
    catalog = load_semantic_catalog()
    metrics = {metric.metric_id: metric for metric in catalog.metrics}

    variance = metrics[MetricName.VARIANCE_AMOUNT]

    assert variance.formula == "actual_expense - budget_expense"
    assert "positive value is unfavorable" in variance.definition.lower()


def test_variance_percent_protects_zero_budget() -> None:
    catalog = load_semantic_catalog()
    metrics = {metric.metric_id: metric for metric in catalog.metrics}

    variance_percent = metrics[MetricName.VARIANCE_PERCENT]

    assert "budget_expense = 0" in variance_percent.formula
    assert any(
        "return null" in guardrail.lower()
        for guardrail in variance_percent.guardrails
    )


def test_cost_per_shipment_requires_weighted_aggregation() -> None:
    catalog = load_semantic_catalog()
    metrics = {metric.metric_id: metric for metric in catalog.metrics}

    for metric_id in (
        MetricName.ACTUAL_COST_PER_SHIPMENT,
        MetricName.BUDGET_COST_PER_SHIPMENT,
    ):
        metric = metrics[metric_id]
        assert metric.aggregation == AggregationRule.WEIGHTED_AVERAGE
        assert "SUM(" in metric.formula


def test_driver_formulas_use_the_approved_decomposition() -> None:
    catalog = load_semantic_catalog()
    metrics = {metric.metric_id: metric for metric in catalog.metrics}

    assert metrics[MetricName.VOLUME_EFFECT].formula == (
        "(actual_shipment_volume - budget_shipment_volume) "
        "* budget_cost_per_shipment"
    )
    assert metrics[MetricName.RATE_EFFECT].formula == (
        "actual_shipment_volume * "
        "(actual_cost_per_shipment - budget_cost_per_shipment)"
    )


def test_duplicate_metric_ids_are_rejected() -> None:
    payload = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
    payload["metrics"].append(payload["metrics"][0])

    with pytest.raises(ValidationError, match="metric_id values must be unique"):
        SemanticCatalog.model_validate(payload)