import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExpectedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    question_class: str | None = None
    selected_skill_name: str | None = None
    result_valid: bool | None = None
    analytics_result: dict[str, str] = Field(default_factory=dict)
    required_tool_suffix: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    final_answer_contains: list[str] = Field(default_factory=list)


class GoldenCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    query: str
    user_id: str
    expected: ExpectedOutcome


class EvaluationResult(BaseModel):
    case_id: str
    passed: bool
    score: float
    checks: dict[str, bool]


def load_cases() -> list[GoldenCase]:
    path = Path(__file__).with_name("dataset.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [GoldenCase.model_validate(item) for item in payload]


def evaluate_result(
    case: GoldenCase,
    result: dict[str, Any],
) -> EvaluationResult:
    expected = case.expected
    trajectory = result.get("tool_trajectory", [])
    answer = result.get("final_answer") or ""
    checks: dict[str, bool] = {
        "status": result.get("status") == expected.status,
    }

    if expected.question_class is not None:
        checks["question_class"] = (
            result.get("question_class") == expected.question_class
        )

    if expected.selected_skill_name is not None:
        checks["selected_skill"] = (
            result.get("selected_skill_name")
            == expected.selected_skill_name
        )

    if expected.result_valid is not None:
        checks["result_valid"] = (
            result.get("result_valid") is expected.result_valid
        )

    observed_data = result.get("analytics_result", {})
    for field, expected_value in expected.analytics_result.items():
        checks[f"result:{field}"] = (
            str(observed_data.get(field)) == expected_value
        )

    if expected.required_tool_suffix:
        suffix_length = len(expected.required_tool_suffix)
        checks["tool_suffix"] = (
            trajectory[-suffix_length:]
            == expected.required_tool_suffix
        )

    for tool_name in expected.forbidden_tools:
        checks[f"forbidden:{tool_name}"] = tool_name not in trajectory

    for fragment in expected.final_answer_contains:
        checks[f"answer:{fragment}"] = fragment.lower() in answer.lower()

    score = sum(checks.values()) / len(checks)
    return EvaluationResult(
        case_id=case.case_id,
        passed=all(checks.values()),
        score=score,
        checks=checks,
    )