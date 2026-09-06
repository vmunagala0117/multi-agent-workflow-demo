import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = (
    PROJECT_ROOT
    / "evals"
    / "medevidence"
    / "groundedness_calibration.jsonl"
)
ALLOWED_LABELS = {"supported", "partial", "unsupported"}


def load_cases() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return [
            json.loads(line)
            for line in dataset_file
            if line.strip()
        ]


def test_groundedness_calibration_is_well_formed_and_balanced() -> None:
    cases = load_cases()

    assert len(cases) >= 9

    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))

    label_counts = Counter(
        case["expected_label"]
        for case in cases
    )
    assert set(label_counts) == ALLOWED_LABELS
    assert all(label_counts[label] >= 3 for label in ALLOWED_LABELS)

    for case in cases:
        assert case["dataset_version"] == "v1"
        assert case["claim"].strip()
        assert case["expected_label"] in ALLOWED_LABELS
        assert case["rationale"].strip()
        assert case["evidence"]

        for evidence in case["evidence"]:
            assert evidence["citation_label"].strip()
            assert evidence["content"].strip()