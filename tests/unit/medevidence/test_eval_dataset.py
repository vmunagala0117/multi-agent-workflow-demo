import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = (
    REPO_ROOT
    / "evals"
    / "medevidence"
    / "cases.jsonl"
)


def load_cases() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in DATASET_PATH.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def test_dataset_has_unique_well_formed_cases() -> None:
    cases = load_cases()

    assert cases

    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))

    for case in cases:
        assert set(case) == {
            "case_id",
            "dataset_version",
            "input",
            "reference",
        }

        assert case["case_id"].strip()
        assert case["dataset_version"] == "v1"

        case_input = case["input"]
        assert case_input["user_query"].strip()
        assert case_input["risk_level"] in {
            "low",
            "high",
        }

        reference = case["reference"]
        assert reference["expected_release_status"] in {
            "released",
            "blocked",
            "review_required",
        }
        assert reference["expected_response_mode"] in {
            "full",
            "abstain",
        }
        assert reference["expected_validation_status"] in {
            "valid",
            "invalid",
        }
        assert reference["minimum_efficacy_findings"] >= 0
        assert reference["minimum_safety_findings"] >= 0