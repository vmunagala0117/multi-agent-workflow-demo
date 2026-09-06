import hashlib
import json
from collections.abc import Callable
from typing import Any

from evals.medevidence.groundedness_judge import (
    GroundednessVerdict,
    judge_groundedness,
)


JudgeFunction = Callable[..., GroundednessVerdict]


def build_evidence_index(outputs: dict) -> dict[str, dict]:
    records = [
        *outputs.get("literature_results", []),
        *outputs.get("internal_evidence", []),
    ]

    return {
        record["citation_label"]: {
            "citation_label": record["citation_label"],
            "content": record["content"],
        }
        for record in records
    }


def collect_findings(outputs: dict) -> list[dict]:
    synthesis = outputs.get("synthesis_result") or {}
    return [
        *synthesis.get("efficacy_findings", []),
        *synthesis.get("safety_findings", []),
    ]


def evaluate_workflow_groundedness(
    inputs: dict,
    outputs: dict,
    *,
    judge: JudgeFunction = judge_groundedness,
) -> list[dict[str, Any]]:
    if outputs.get("release_status") != "released":
        return [
            {
                "key": "groundedness_evaluated",
                "score": False,
                "comment": (
                    "Not applicable because the workflow did not "
                    "release a synthesis."
                ),
            }
        ]

    findings = collect_findings(outputs)
    if not findings:
        raise ValueError(
            "Released workflow output contains no cited findings."
        )

    evidence_index = build_evidence_index(outputs)
    query_hash = hashlib.sha256(
        inputs["user_query"].encode("utf-8")
    ).hexdigest()[:12]

    details = []
    for finding_number, finding in enumerate(findings, start=1):
        citation_labels = finding.get("citation_labels", [])
        missing_labels = [
            label
            for label in citation_labels
            if label not in evidence_index
        ]

        if missing_labels:
            details.append(
                {
                    "finding": finding["finding"],
                    "citation_labels": citation_labels,
                    "label": "unsupported",
                    "rationale": (
                        "Citation labels were absent from the retrieved "
                        f"evidence: {missing_labels}"
                    ),
                }
            )
            continue

        selected_evidence = [
            evidence_index[label]
            for label in citation_labels
        ]
        verdict = judge(
            claim=finding["finding"],
            evidence=selected_evidence,
            case_id=f"{query_hash}-finding-{finding_number}",
        )
        details.append(
            {
                "finding": finding["finding"],
                "citation_labels": citation_labels,
                "label": verdict.label,
                "rationale": verdict.rationale,
            }
        )

    total = len(details)
    supported = sum(
        item["label"] == "supported"
        for item in details
    )
    partial_or_better = sum(
        item["label"] in {"supported", "partial"}
        for item in details
    )
    unsupported = sum(
        item["label"] == "unsupported"
        for item in details
    )
    comment = json.dumps(details, indent=2)

    return [
        {
            "key": "groundedness_evaluated",
            "score": True,
        },
        {
            "key": "grounded_claim_rate",
            "score": supported / total,
            "comment": comment,
        },
        {
            "key": "partial_or_better_rate",
            "score": partial_or_better / total,
        },
        {
            "key": "no_unsupported_claims",
            "score": unsupported == 0,
        },
    ]