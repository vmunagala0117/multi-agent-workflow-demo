import pytest

from use_cases.medevidence_research.tools.retrieval import (
    load_corpus,
    search_internal_evidence,
    search_literature,
)


QUERY = (
    "What evidence supports Therapy Alpha for reducing chronic "
    "pruritus in adults, and what safety limitations remain?"
)


def test_corpora_load_successfully() -> None:
    assert len(load_corpus("literature")) == 3
    assert len(load_corpus("internal_evidence")) == 3


def test_literature_search_ranks_relevant_trial_first() -> None:
    results = search_literature(QUERY, top_k=2)

    assert results
    assert results[0]["source_id"] == "LIT-001"
    assert "LIT-003" not in {
        result["source_id"] for result in results
    }

    assert results[0]["retrieval_score"] >= (
        results[1]["retrieval_score"]
    )


def test_internal_search_excludes_restricted_and_superseded() -> None:
    results = search_internal_evidence(QUERY, top_k=3)

    result_ids = {result["source_id"] for result in results}

    assert result_ids == {"INT-001", "INT-002"}
    assert "INT-003" not in result_ids

    assert all(
        result["access_level"] == "internal"
        for result in results
    )

    assert all(
        result["metadata"]["status"] == "approved"
        for result in results
    )


def test_empty_query_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Search query cannot be empty",
    ):
        search_literature("   ")