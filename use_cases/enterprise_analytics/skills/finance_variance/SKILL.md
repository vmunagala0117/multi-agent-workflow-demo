---
name: finance_variance
version: 1.0.0
description: Analyze governed expense-versus-budget variance and rank business-unit contributions.
domain: finance
question_classes:
  - finance_variance
  - business_unit_contribution
required_metrics:
  - actual_expense
  - budget_expense
  - variance_amount
  - variance_percent
allowed_tools:
  - get_metric_definition
  - get_dataset_schema
  - validate_query
  - execute_analytics_query
  - validate_result
---

# Finance Variance Skill

## Use this skill when

- The user asks why actual expense differs from budget.
- The user asks which business units contributed most to a variance.
- The requested domain is finance and the authorization layer has approved finance access.

## Do not use this skill when

- The question asks whether shipment volume or unit cost caused the variance.
- The request is outside the governed finance metrics or authorized scope.
- The period, region, or cost category cannot be resolved safely.

## Procedure

1. Retrieve the governed definitions for actual expense, budget expense, variance amount, and variance percent.
2. Retrieve the allowed dataset schema and join paths.
3. Produce a structured query plan; never produce free-form executable SQL as the control contract.
4. Apply the user's authorized organizational scope.
5. Validate the query plan before execution.
6. Execute only through the governed analytics tool.
7. Validate totals and confirm that variance equals actual minus budget.
8. For contribution questions, rank business units by variance amount using validated results.
9. Clarify or abstain if definitions, access, filters, or validation are insufficient.

## Governing rules

- Expense variance is `actual_expense - budget_expense`.
- A positive expense variance is unfavorable; a negative expense variance is favorable.
- Variance percent is calculated from aggregated totals, not averaged from row-level percentages.
- Never broaden the user's region, period, business-unit, or cost-category scope.
- Do not claim causality from finance variance alone.
- Only use tools listed in this skill's `allowed_tools` metadata.

## Expected response content

- Requested scope and reporting period
- Actual expense and budget expense
- Variance amount and variance percent
- Favorable or unfavorable direction
- Ranked business-unit contributions when requested
- Definition version and validation status