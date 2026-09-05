from pprint import pprint

from use_cases.medevidence_research.graph import build_graph


def main() -> None:
    graph = build_graph()

    initial_state = {
        "user_query": (
            "What evidence supports Therapy Alpha for reducing chronic "
            "pruritus in adults, and what safety limitations remain?"
        ),
        "risk_level": "low",
        "literature_results": [],
        "internal_evidence": [],
        "evidence_status": None,
        "response_mode": None,
        "synthesis": None,
        "citations": [],
        "validation_status": None,
        "errors": [],
    }

    final_state = graph.invoke(initial_state)
    pprint(final_state)


if __name__ == "__main__":
    main()