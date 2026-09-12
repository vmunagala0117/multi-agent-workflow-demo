from pathlib import Path

from use_cases.enterprise_analytics.schemas import SemanticCatalog


DEFAULT_CATALOG_PATH = (
    Path(__file__).parent / "data" / "semantic_definitions.json"
)


def load_semantic_catalog(
    path: Path = DEFAULT_CATALOG_PATH,
) -> SemanticCatalog:
    return SemanticCatalog.model_validate_json(
        path.read_text(encoding="utf-8")
    )