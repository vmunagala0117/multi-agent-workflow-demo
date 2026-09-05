# MedEvidence Evaluation Dataset

## Purpose

This dataset measures the MedEvidence workflow against synthetic evidence only.
It must not contain patient data, confidential client data, or real internal
medical documents.

## Row Contract

- `case_id`: stable unique identifier
- `dataset_version`: version of the labeled dataset
- `input.user_query`: question supplied to the workflow
- `input.risk_level`: explicit risk classification used by policy routing
- `reference.expected_release_status`: expected release-gate outcome
- `reference.expected_response_mode`: expected evidence-completeness mode
- `reference.expected_validation_status`: expected citation-validation result
- `reference.minimum_efficacy_findings`: minimum structured efficacy findings
- `reference.minimum_safety_findings`: minimum structured safety findings

## Labeling Rules

1. Expectations are defined from the use-case policy and synthetic source data,
   not copied from a model response.
2. A schema-valid response is not automatically considered grounded.
3. Exact prose matching is not used because multiple supported formulations may
   be correct.
4. Changes to expectations require a dataset-version update and review.
5. New cases should represent a new risk or observed failure mode.