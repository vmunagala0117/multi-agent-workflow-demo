import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = (
    PROJECT_ROOT / "evals" / "medevidence" / "cases.jsonl"
)


def load_cases() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return [
            json.loads(line)
            for line in dataset_file
            if line.strip()
        ]


def test_dataset_has_unique_well_formed_cases() -> None:
    cases = load_cases()

    assert cases

    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))

    for case in cases:
        assert case["dataset_version"] == "v1"
        assert case["input"]["user_query"].strip()
        assert case["input"]["risk_level"] in {
            "low",
            "medium",
            "high",
        }

        reference = case["reference"]
        assert reference["expected_release_status"] in {
            "released",
            "blocked",
            "abstained",
            "rejected",
        }
        assert reference["expected_response_mode"] in {
            "full",
            "partial",
            "abstain",
        }
        assert reference["expected_validation_status"] in {
            "valid",
            "invalid",
            "not_applicable",
        }
        assert reference["minimum_efficacy_findings"] >= 0
        assert reference["minimum_safety_findings"] >= 0