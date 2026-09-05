from typing import Any


def _as_dict(value: Any) -> dict:
    if value is None:
        return {}

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if isinstance(value, dict):
        return value

    raise TypeError(
        "synthesis_result must be a Pydantic model or dictionary."
    )


def _binary(condition: bool) -> float:
    return 1.0 if condition else 0.0


def evaluate_case(
    output: dict,
    reference: dict,
) -> dict[str, float]:
    result = _as_dict(output.get("synthesis_result"))

    efficacy_findings = result.get("efficacy_findings", [])
    safety_findings = result.get("safety_findings", [])
    all_findings = [*efficacy_findings, *safety_findings]

    allowed_labels = {
        record["citation_label"]
        for record in [
            *output.get("literature_results", []),
            *output.get("internal_evidence", []),
        ]
    }

    cited_labels = [
        label
        for finding in all_findings
        for label in finding.get("citation_labels", [])
    ]

    cited_finding_count = sum(
        bool(finding.get("citation_labels"))
        for finding in all_findings
    )

    finding_citation_coverage = (
        cited_finding_count / len(all_findings)
        if all_findings
        else 0.0
    )

    valid_citation_rate = (
        sum(label in allowed_labels for label in cited_labels)
        / len(cited_labels)
        if cited_labels
        else 0.0
    )

    scores = {
        "release_status_match": _binary(
            output.get("release_status")
            == reference["expected_release_status"]
        ),
        "response_mode_match": _binary(
            output.get("response_mode")
            == reference["expected_response_mode"]
        ),
        "validation_status_match": _binary(
            output.get("validation_status")
            == reference["expected_validation_status"]
        ),
        "efficacy_minimum_met": _binary(
            len(efficacy_findings)
            >= reference["minimum_efficacy_findings"]
        ),
        "safety_minimum_met": _binary(
            len(safety_findings)
            >= reference["minimum_safety_findings"]
        ),
        "finding_citation_coverage": finding_citation_coverage,
        "valid_citation_rate": valid_citation_rate,
    }

    scores["overall_pass"] = _binary(
        all(score == 1.0 for score in scores.values())
    )

    return scores