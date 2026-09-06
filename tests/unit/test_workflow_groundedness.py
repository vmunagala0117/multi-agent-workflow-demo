from types import SimpleNamespace

from evals.medevidence.workflow_groundedness import (
    evaluate_workflow_groundedness,
)


def released_output() -> dict:
    return {
        "release_status": "released",
        "synthesis_result": {
            "efficacy_findings": [
                {
                    "finding": "Supported efficacy finding.",
                    "citation_labels": ["[LIT-001]"],
                }
            ],
            "safety_findings": [
                {
                    "finding": "Partially supported safety finding.",
                    "citation_labels": ["[INT-002]"],
                }
            ],
        },
        "literature_results": [
            {
                "citation_label": "[LIT-001]",
                "content": "Synthetic efficacy evidence.",
            }
        ],
        "internal_evidence": [
            {
                "citation_label": "[INT-002]",
                "content": "Synthetic safety evidence.",
            }
        ],
    }


def test_aggregates_finding_level_verdicts() -> None:
    verdicts = iter(
        [
            SimpleNamespace(
                label="supported",
                rationale="Directly supported.",
            ),
            SimpleNamespace(
                label="partial",
                rationale="One qualifier is overstated.",
            ),
        ]
    )

    def fake_judge(**kwargs):
        return next(verdicts)

    results = evaluate_workflow_groundedness(
        {"user_query": "Synthetic question"},
        released_output(),
        judge=fake_judge,
    )
    scores = {
        result["key"]: result["score"]
        for result in results
    }

    assert scores["groundedness_evaluated"] is True
    assert scores["grounded_claim_rate"] == 0.5
    assert scores["partial_or_better_rate"] == 1.0
    assert scores["no_unsupported_claims"] is True


def test_unknown_citation_is_unsupported_without_judge_call() -> None:
    output = released_output()
    output["synthesis_result"]["efficacy_findings"] = [
        {
            "finding": "Finding with invented citation.",
            "citation_labels": ["[LIT-999]"],
        }
    ]
    output["synthesis_result"]["safety_findings"] = []

    def fail_if_called(**kwargs):
        raise AssertionError("Judge should not be called.")

    results = evaluate_workflow_groundedness(
        {"user_query": "Synthetic question"},
        output,
        judge=fail_if_called,
    )
    scores = {
        result["key"]: result["score"]
        for result in results
    }

    assert scores["grounded_claim_rate"] == 0.0
    assert scores["no_unsupported_claims"] is False