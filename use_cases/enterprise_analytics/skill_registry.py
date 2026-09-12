from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    MetricName,
    QuestionClass,
)


DEFAULT_SKILLS_DIR = Path(__file__).parent / "skills"


class SkillRegistryError(ValueError):
    pass


class SkillMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(min_length=1)
    domain: AnalyticsDomain
    question_classes: set[QuestionClass] = Field(min_length=1)
    required_metrics: set[MetricName] = Field(min_length=1)
    allowed_tools: set[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_question_domain_alignment(self) -> "SkillMetadata":
        finance_questions = {
            QuestionClass.FINANCE_VARIANCE,
            QuestionClass.BUSINESS_UNIT_CONTRIBUTION,
        }
        if self.question_classes & finance_questions:
            if self.domain != AnalyticsDomain.FINANCE:
                raise ValueError(
                    "finance question classes require the finance domain"
                )
        if QuestionClass.OPERATIONS_DRIVER in self.question_classes:
            if self.domain != AnalyticsDomain.OPERATIONS:
                raise ValueError(
                    "operations_driver requires the operations domain"
                )
        return self


class RegisteredSkill(BaseModel):
    metadata: SkillMetadata
    path: Path


class LoadedSkill(BaseModel):
    metadata: SkillMetadata
    instructions: str = Field(min_length=1)


def _read_front_matter(path: Path) -> SkillMetadata:
    lines: list[str] = []

    with path.open(encoding="utf-8") as handle:
        if handle.readline().strip() != "---":
            raise SkillRegistryError(
                f"Skill file {path} is missing YAML front matter"
            )

        for line in handle:
            if line.strip() == "---":
                break
            lines.append(line)
        else:
            raise SkillRegistryError(
                f"Skill file {path} has unterminated YAML front matter"
            )

    payload = yaml.safe_load("".join(lines))
    if not isinstance(payload, dict):
        raise SkillRegistryError(f"Skill metadata in {path} is invalid")

    return SkillMetadata.model_validate(payload)


def _read_instructions(path: Path) -> str:
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise SkillRegistryError(
            f"Skill file {path} is missing YAML front matter"
        )

    try:
        _, instructions = normalized[4:].split("\n---\n", maxsplit=1)
    except ValueError as exc:
        raise SkillRegistryError(
            f"Skill file {path} has unterminated YAML front matter"
        ) from exc

    instructions = instructions.strip()
    if not instructions:
        raise SkillRegistryError(f"Skill file {path} has no instructions")
    return instructions


class SkillRegistry:
    def __init__(self, skills_dir: Path = DEFAULT_SKILLS_DIR) -> None:
        self._skills_dir = skills_dir
        self._skills = self._discover()

    def _discover(self) -> dict[str, RegisteredSkill]:
        discovered: dict[str, RegisteredSkill] = {}

        for path in sorted(self._skills_dir.glob("*/SKILL.md")):
            metadata = _read_front_matter(path)
            if metadata.name in discovered:
                raise SkillRegistryError(
                    f"Duplicate skill name: {metadata.name}"
                )
            discovered[metadata.name] = RegisteredSkill(
                metadata=metadata,
                path=path,
            )

        if not discovered:
            raise SkillRegistryError(
                f"No skills found under {self._skills_dir}"
            )
        return discovered

    def list_metadata(self) -> list[SkillMetadata]:
        return [
            registered.metadata
            for registered in self._skills.values()
        ]

    def list_eligible_metadata(
        self,
        allowed_domains: set[AnalyticsDomain],
    ) -> list[SkillMetadata]:
        return [
            registered.metadata
            for registered in self._skills.values()
            if registered.metadata.domain in allowed_domains
        ]

    def select(
        self,
        *,
        question_class: QuestionClass,
        allowed_domains: set[AnalyticsDomain],
    ) -> LoadedSkill:
        candidates = [
            registered
            for registered in self._skills.values()
            if registered.metadata.domain in allowed_domains
            and question_class in registered.metadata.question_classes
        ]

        if len(candidates) != 1:
            raise SkillRegistryError(
                "Expected exactly one authorized skill for "
                f"{question_class}; found {len(candidates)}"
            )

        selected = candidates[0]
        return LoadedSkill(
            metadata=selected.metadata,
            instructions=_read_instructions(selected.path),
        )