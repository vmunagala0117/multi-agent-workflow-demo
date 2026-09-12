---
name: operations_performance
version: 1.0.0
description: Determine whether shipment volume or cost per shipment drove a governed logistics expense variance.
domain: operations
question_classes:
  - operations_driver
required_metrics:
  - actual_shipment_volume
  - budget_shipment_volume
  - actual_cost_per_shipment
  - budget_cost_per_shipment
  - volume_effect
  - rate_effect
allowed_tools:
  - get_metric_definition
  - get_dataset_schema
  - validate_query
  - execute_analytics_query
  - validate_result
---

# Operations Performance Skill

## Use this skill when

- The user asks whether shipment volume or cost per shipment drove logistics variance.
- The requested domain is operations and the authorization layer has approved operations access.

## Do not use this skill when

- The user asks only for actual-versus-budget finance totals or contribution ranking.
- The required operational metrics are missing or outside the user's authorized scope.
- Finance and operations results cannot be reconciled for the same period and organization.

## Procedure

1. Retrieve definitions for actual and budget shipment volume, actual and budget cost per shipment, volume effect, and rate effect.
2. Retrieve the governed operations schema and its approved relationship to finance scope.
3. Produce a structured query plan with the same period and organizational filters across facts.
4. Validate the plan before execution.
5. Execute only through the governed analytics tool.
6. Calculate volume and rate effects using the approved semantic formulas.
7. Validate that volume effect plus rate effect equals total finance variance.
8. Identify the primary driver by absolute contribution, not narrative intuition.
9. Clarify or abstain if reconciliation fails.

## Governing rules

- Volume effect is `(actual_volume - budget_volume) * budget_cost_per_shipment`.
- Rate effect is `actual_volume * (actual_cost_per_shipment - budget_cost_per_shipment)`.
- The interaction effect is assigned to rate under the approved definition.
- Cost per shipment must be volume-weighted across business units.
- Do not compare facts from different periods or organizational scopes.
- Only use tools listed in this skill's `allowed_tools` metadata.

## Expected response content

- Requested scope and reporting period
- Total validated finance variance
- Shipment-volume effect
- Cost-per-shipment effect
- Primary driver and its share of the total variance
- Reconciliation and definition-version status