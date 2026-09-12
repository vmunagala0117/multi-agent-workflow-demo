import pytest

from use_cases.enterprise_analytics.schemas import (
    AnalyticsDomain,
    MetricName,
    QuestionClass,
)
from use_cases.enterprise_analytics.skill_registry import (
    SkillRegistry,
    SkillRegistryError,
)


@pytest.fixture
def registry() -> SkillRegistry:
    return SkillRegistry()


def test_discovers_two_governed_skills(registry: SkillRegistry) -> None:
    metadata = registry.list_metadata()
    assert {skill.name for skill in metadata} == {
        "finance_variance",
        "operations_performance",
    }


def test_discovery_returns_metadata_not_instruction_bodies(
    registry: SkillRegistry,
) -> None:
    metadata = registry.list_metadata()
    assert all(not hasattr(skill, "instructions") for skill in metadata)


def test_selects_finance_skill_for_variance(
    registry: SkillRegistry,
) -> None:
    selected = registry.select(
        question_class=QuestionClass.FINANCE_VARIANCE,
        allowed_domains={AnalyticsDomain.FINANCE},
    )

    assert selected.metadata.name == "finance_variance"
    assert "actual_expense - budget_expense" in selected.instructions


def test_selects_operations_skill_for_driver_question(
    registry: SkillRegistry,
) -> None:
    selected = registry.select(
        question_class=QuestionClass.OPERATIONS_DRIVER,
        allowed_domains={AnalyticsDomain.OPERATIONS},
    )

    assert selected.metadata.name == "operations_performance"
    assert MetricName.RATE_EFFECT in selected.metadata.required_metrics
    assert "reconcile" in selected.instructions.lower()


def test_unauthorized_domain_fails_closed(registry: SkillRegistry) -> None:
    with pytest.raises(
        SkillRegistryError,
        match="found 0",
    ):
        registry.select(
            question_class=QuestionClass.FINANCE_VARIANCE,
            allowed_domains={AnalyticsDomain.OPERATIONS},
        )


def test_finance_skill_does_not_claim_operations_questions(
    registry: SkillRegistry,
) -> None:
    finance = next(
        skill
        for skill in registry.list_metadata()
        if skill.name == "finance_variance"
    )
    assert QuestionClass.OPERATIONS_DRIVER not in finance.question_classes


def test_selected_skill_has_bounded_tool_allowlist(
    registry: SkillRegistry,
) -> None:
    selected = registry.select(
        question_class=QuestionClass.BUSINESS_UNIT_CONTRIBUTION,
        allowed_domains={AnalyticsDomain.FINANCE},
    )

    assert selected.metadata.allowed_tools == {
        "get_metric_definition",
        "get_dataset_schema",
        "validate_query",
        "execute_analytics_query",
        "validate_result",
    }