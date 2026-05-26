from __future__ import annotations


def format_context(
    selected_processes: list[str],
    requirements_summary: str,
    extra_context: str = "",
) -> str:
    """Assemble the enriched context string passed to downstream agents (Agent 3 — no LLM)."""
    parts = [
        "PROCESSUS SELECTIONNES : " + ", ".join(selected_processes),
        "RESUME CADRE REGLEMENTAIRE :\n" + requirements_summary,
    ]
    if extra_context:
        parts.append(extra_context)
    return "\n\n".join(parts).strip()
