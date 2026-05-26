from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from module_folder.models import RequirementAnalysis, SingleRequirementFeedback

_PROMPT_FILE = Path(__file__).parent.parent.parent / "Prompt agent 3.txt"
_SYSTEM: str = _PROMPT_FILE.read_text(encoding="utf-8")

DEFAULT_SYSTEM = _SYSTEM


def evaluate_requirement(
    analysis: RequirementAnalysis,
    procedure_text: str,
    extra_context: str = "",
    *,
    llm,
    system_prompt: str | None = None,
) -> SingleRequirementFeedback:
    """Quality-check an analysis and decide whether it needs a re-run (Agent 5)."""
    ctx = f"\n\nCONTEXTE:\n{extra_context[:3000]}" if extra_context else ""
    user = (
        f"Procedure:\n{procedure_text[:5000]}\n\n"
        f"Exigence [{analysis.requirement_id}]: {analysis.requirement_text[:300]}\n"
        f"Conformite: {analysis.compliance_level} | Criticite: {analysis.criticite} | Priorite: {analysis.priorite}\n"
        f"Preuve: {analysis.preuve_constat[:400]}\n"
        f"Ecart: {analysis.ecart_description[:300]}\n"
        f"Recommandation: {analysis.recommandation[:300]}{ctx}"
    )
    return llm.with_structured_output(SingleRequirementFeedback).invoke(
        [SystemMessage(content=system_prompt or _SYSTEM), HumanMessage(content=user)]
    )
