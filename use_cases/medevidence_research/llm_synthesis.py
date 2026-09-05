import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.azure_openai import get_azure_chat_model

from .schemas import EvidenceSynthesis
from .state import MedicalResearchState


SYSTEM_PROMPT = """You are a medical evidence synthesis assistant.
Use only the evidence records supplied by the workflow.
Do not add outside medical knowledge or invent facts.
Every efficacy and safety finding must contain one or more citation labels
copied exactly from the supplied evidence.
Describe missing or insufficient evidence under evidence_gaps.
Keep conclusions appropriately qualified and do not provide patient-specific advice.
"""


def render_synthesis(result: EvidenceSynthesis) -> str:
    lines = [result.executive_summary, "", "Efficacy findings:"]

    lines.extend(
        f"- {item.finding} {' '.join(item.citation_labels)}"
        for item in result.efficacy_findings
    )
    lines.append("")
    lines.append("Safety findings:")
    lines.extend(
        f"- {item.finding} {' '.join(item.citation_labels)}"
        for item in result.safety_findings
    )
    lines.append("")
    lines.append("Evidence gaps:")
    lines.extend(f"- {gap}" for gap in result.evidence_gaps)
    lines.append("")
    lines.append("Limitations:")
    lines.extend(f"- {limitation}" for limitation in result.limitations)

    return "\n".join(lines)


def synthesize_with_llm(state: MedicalResearchState) -> dict:
    allowed_labels = [
        record["citation_label"]
        for record in [
            *state["literature_results"],
            *state["internal_evidence"],
        ]
    ]

    evidence_payload = {
        "user_query": state["user_query"],
        "allowed_citation_labels": allowed_labels,
        "literature_results": state["literature_results"],
        "internal_evidence": state["internal_evidence"],
    }

    structured_model = get_azure_chat_model().with_structured_output(
        EvidenceSynthesis,
        method="json_schema",
    )

    result = structured_model.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Answer the query using only this workflow evidence:\n"
                    + json.dumps(evidence_payload, indent=2)
                )
            ),
        ]
    )

    if not isinstance(result, EvidenceSynthesis):
        result = EvidenceSynthesis.model_validate(result)

    return {
        "synthesis_result": result,
        "synthesis": render_synthesis(result),
        "validation_status": "not_validated",
    }