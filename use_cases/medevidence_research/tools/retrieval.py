import json
import re
from pathlib import Path
from typing import Literal, cast

from ..models import EvidenceRecord


CorpusName = Literal["literature", "internal_evidence"]

DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"

CORPUS_FILES: dict[CorpusName, str] = {
    "literature": "literature.json",
    "internal_evidence": "internal_evidence.json",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "what",
    "with",
}


def tokenize(text: str) -> set[str]:
    """Normalize text into unique searchable terms."""

    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return tokens - STOP_WORDS


def load_corpus(corpus_name: CorpusName) -> list[EvidenceRecord]:
    """Load one normalized evidence corpus from disk."""

    corpus_path = DATA_DIRECTORY / CORPUS_FILES[corpus_name]

    with corpus_path.open(encoding="utf-8") as corpus_file:
        records = json.load(corpus_file)

    if not isinstance(records, list):
        raise ValueError(
            f"Corpus must contain a JSON list: {corpus_path}"
        )

    return cast(list[EvidenceRecord], records)


def calculate_relevance_score(
    query: str,
    record: EvidenceRecord,
) -> float:
    """Calculate a transparent lexical relevance score."""

    query_tokens = tokenize(query)
    title_tokens = tokenize(record["title"])
    content_tokens = tokenize(record["content"])

    metadata_text = " ".join(record.get("metadata", {}).values())
    metadata_tokens = tokenize(metadata_text)

    title_overlap = len(query_tokens & title_tokens)
    content_overlap = len(query_tokens & content_tokens)
    metadata_overlap = len(query_tokens & metadata_tokens)

    return (
        (title_overlap * 3.0)
        + content_overlap
        + (metadata_overlap * 0.5)
    )


def search_corpus(
    *,
    query: str,
    corpus_name: CorpusName,
    top_k: int,
    allowed_access_levels: set[str],
    required_status: str | None = None,
) -> list[EvidenceRecord]:
    """Filter and rank one corpus using explicit retrieval rules."""

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    eligible_records: list[EvidenceRecord] = []

    for record in load_corpus(corpus_name):
        if record.get("access_level") not in allowed_access_levels:
            continue

        metadata = record.get("metadata", {})

        if (
            required_status is not None
            and metadata.get("status") != required_status
        ):
            continue

        score = calculate_relevance_score(query, record)

        if score <= 0:
            continue

        ranked_record = dict(record)
        ranked_record["retrieval_score"] = score

        eligible_records.append(
            cast(EvidenceRecord, ranked_record)
        )

    eligible_records.sort(
        key=lambda record: (
            record.get("retrieval_score", 0.0),
            record.get("published_date", ""),
        ),
        reverse=True,
    )

    return eligible_records[:top_k]


def search_literature(
    query: str,
    top_k: int = 2,
) -> list[EvidenceRecord]:
    """Search eligible public literature."""

    return search_corpus(
        query=query,
        corpus_name="literature",
        top_k=top_k,
        allowed_access_levels={"public"},
    )


def search_internal_evidence(
    query: str,
    top_k: int = 2,
) -> list[EvidenceRecord]:
    """Search current, approved internal evidence."""

    return search_corpus(
        query=query,
        corpus_name="internal_evidence",
        top_k=top_k,
        allowed_access_levels={"internal"},
        required_status="approved",
    )