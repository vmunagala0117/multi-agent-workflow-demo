from typing import Literal, NotRequired, TypedDict


class EvidenceRecord(TypedDict):
    """Normalized evidence returned by any retrieval tool."""

    source_id: str
    source_type: Literal["literature", "internal"]

    title: str
    content: str
    citation_label: str

    published_date: NotRequired[str]
    source_uri: NotRequired[str]
    document_version: NotRequired[str]
    access_level: NotRequired[str]

    retrieval_score: NotRequired[float]
    metadata: NotRequired[dict[str, str]]