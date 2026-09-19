from dotenv import load_dotenv
from langsmith import Client

from evals.enterprise_analytics.evaluators import load_cases


DATASET_NAME = "enterpriseops-golden-v1"


def main() -> None:
    load_dotenv()
    client = Client()

    datasets = list(
        client.list_datasets(dataset_name=DATASET_NAME)
    )
    if datasets:
        dataset = datasets[0]
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description=(
                "Versioned EnterpriseOps routing, authorization, "
                "numeric-result, and trajectory contracts."
            ),
        )

    existing_case_ids = {
        example.metadata.get("case_id")
        for example in client.list_examples(dataset_id=dataset.id)
        if example.metadata
    }

    examples = []
    for case in load_cases():
        if case.case_id in existing_case_ids:
            continue
        examples.append(
            {
                "inputs": {
                    "case_id": case.case_id,
                    "query": case.query,
                    "user_id": case.user_id,
                },
                "outputs": {
                    "expected": case.expected.model_dump(mode="json"),
                },
                "metadata": {
                    "case_id": case.case_id,
                    "dataset_version": "v1",
                },
            }
        )

    if examples:
        client.create_examples(
            dataset_id=dataset.id,
            examples=examples,
        )

    print(
        f"Dataset {DATASET_NAME}: "
        f"added {len(examples)} new case(s)"
    )


if __name__ == "__main__":
    main()