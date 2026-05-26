from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from module_folder.models import SingleValidationResult

_PROMPT_FILE = Path(__file__).parent.parent.parent / "PROMPT AGENT 1 SCOPER.txt"
_SYSTEM: str = _PROMPT_FILE.read_text(encoding="utf-8")

DEFAULT_SYSTEM = _SYSTEM


def run_validateur_one(
    req_id: str,
    req_text: str,
    procedure_context: str,
    selected_processes: list[str],
    *,
    llm,
    system_prompt: str | None = None,
) -> SingleValidationResult:
    """Decide whether a single requirement is relevant to the procedure (Agent 1)."""
    user = (
        f"Processus selectionnes: {', '.join(selected_processes)}\n\n"
        f"Extrait procedure:\n{procedure_context[:6000]}\n\n"
        f"Exigence [{req_id}]:\n{req_text}"
    )
    return llm.with_structured_output(SingleValidationResult).invoke(
        [SystemMessage(content=system_prompt or _SYSTEM), HumanMessage(content=user)]
    )
