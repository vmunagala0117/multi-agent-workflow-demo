import json
from collections import Counter
from pathlib import Path

from evals.medevidence.groundedness_judge import (
    GroundednessLabel,
    judge_groundedness,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = (
    PROJECT_ROOT
    / "evals"
    / "medevidence"
    / "groundedness_calibration.jsonl"
)
LABELS: tuple[GroundednessLabel, ...] = (
    "supported",
    "partial",
    "unsupported",
)

# Provisional demo thresholds, not production clinical validation criteria.
MIN_OVERALL_ACCURACY = 0.80
MIN_UNSUPPORTED_RECALL = 1.00


def load_cases() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return [
            json.loads(line)
            for line in dataset_file
            if line.strip()
        ]


def safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def main() -> None:
    cases = load_cases()
    confusion = {
        actual: Counter({predicted: 0 for predicted in LABELS})
        for actual in LABELS
    }
    correct = 0
    severe_errors = 0

    for case in cases:
        verdict = judge_groundedness(
            claim=case["claim"],
            evidence=case["evidence"],
            case_id=case["case_id"],
        )

        expected = case["expected_label"]
        predicted = verdict.label
        confusion[expected][predicted] += 1
        correct += int(predicted == expected)

        if expected == "unsupported" and predicted == "supported":
            severe_errors += 1

        print(
            json.dumps(
                {
                    "case_id": case["case_id"],
                    "expected": expected,
                    "predicted": predicted,
                    "correct": predicted == expected,
                    "judge_rationale": verdict.rationale,
                },
                indent=2,
            )
        )

    accuracy = safe_divide(correct, len(cases))

    print("\nConfusion matrix (rows=actual, columns=predicted)")
    print("actual\\predicted", *LABELS, sep="\t")
    for actual in LABELS:
        print(
            actual,
            *(confusion[actual][predicted] for predicted in LABELS),
            sep="\t",
        )

    metrics = {}
    for label in LABELS:
        true_positive = confusion[label][label]
        actual_total = sum(confusion[label].values())
        predicted_total = sum(
            confusion[actual][label]
            for actual in LABELS
        )
        metrics[label] = {
            "precision": safe_divide(
                true_positive,
                predicted_total,
            ),
            "recall": safe_divide(
                true_positive,
                actual_total,
            ),
        }

    summary = {
        "total_cases": len(cases),
        "overall_accuracy": accuracy,
        "per_label": metrics,
        "unsupported_as_supported": severe_errors,
    }
    print("\nSummary")
    print(json.dumps(summary, indent=2))

    passed = (
        accuracy >= MIN_OVERALL_ACCURACY
        and metrics["unsupported"]["recall"]
        >= MIN_UNSUPPORTED_RECALL
        and severe_errors == 0
    )

    if not passed:
        raise SystemExit(
            "Groundedness judge did not meet the provisional gate."
        )


if __name__ == "__main__":
    main()