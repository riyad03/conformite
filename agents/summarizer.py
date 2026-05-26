from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

_SYSTEM = """\
Tu es un expert en droit et conformite reglementaire GRC. Analyse l'ensemble des exigences
reglementaires fournies et redige un resume structure de 400-500 mots qui met en evidence :
- Les thematiques et obligations principales du cadre reglementaire
- Les droits et protections accordes aux personnes concernees
- Les obligations des responsables de traitement
- Les controles, sanctions et mecanismes de supervision prevus
- Les points de vigilance et exigences les plus contraignantes
Sois factuel et exhaustif pour permettre une evaluation de conformite precise des procedures internes.\
"""

DEFAULT_SYSTEM = _SYSTEM


def summarize_requirements(requirements: dict[str, str], *, llm, system_prompt: str | None = None) -> str:
    """Produce a structured summary of the regulatory framework (Agent 2)."""
    req_text = "\n\n".join(f"[{rid}]\n{rtxt}" for rid, rtxt in requirements.items())
    response = llm.invoke([
        SystemMessage(content=system_prompt or _SYSTEM),
        HumanMessage(content=f"Exigences reglementaires a resumer :\n\n{req_text[:20000]}"),
    ])
    return response.content
