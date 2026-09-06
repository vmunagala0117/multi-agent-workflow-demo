import json
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "evals" / "medevidence" / "cases.jsonl"
DATASET_NAME = "medevidence-golden-v1"

load_dotenv(PROJECT_ROOT / ".env")

from langsmith import Client


def load_cases() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return [
            json.loads(line)
            for line in dataset_file
            if line.strip()
        ]


def main() -> None:
    cases = load_cases()
    client = Client()

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=(
            "Version 1 golden cases for the synthetic MedEvidence "
            "workflow. Contains no patient or client data."
        ),
    )

    examples = [
        {
            "inputs": case["input"],
            "outputs": case["reference"],
            "metadata": {
                "case_id": case["case_id"],
                "dataset_version": case["dataset_version"],
            },
        }
        for case in cases
    ]

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    print(f"Created dataset: {dataset.name}")
    print(f"Published examples: {len(examples)}")


if __name__ == "__main__":
    main()