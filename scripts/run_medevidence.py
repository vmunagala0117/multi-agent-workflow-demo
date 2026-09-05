from pprint import pprint

from use_cases.medevidence_research.graph import build_graph
from use_cases.medevidence_research.llm_synthesis import synthesize_with_llm


def main() -> None:
    graph = build_graph(synthesis_node=synthesize_with_llm)

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
        "synthesis_result": None,
        "citations": [],
        "validation_status": None,
        "errors": [],
    }

    final_state = graph.invoke(initial_state)
    pprint(final_state)


if __name__ == "__main__":
    main()