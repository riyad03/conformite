from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .analyzer import analyze_compliance
from .extractor import extract_texts
from .reporter import generate_report
from .state import ConformiteState


def _route_score(state: ConformiteState) -> str:
    return "conforme" if state["score_conformite"] >= 80 else "a_valider"


def envoie_au_CO(state: ConformiteState) -> dict:
    """Placeholder: queue low-scoring procedures for compliance officer review."""
    print(f"  [CO] En attente de validation (score={state['score_conformite']})")
    return {}


def build_agent():
    g = StateGraph(ConformiteState)

    g.add_node("extract_texts",      extract_texts)
    g.add_node("analyze_compliance", analyze_compliance)
    g.add_node("generate_report",    generate_report)
    g.add_node("envoie_au_CO",       envoie_au_CO)

    g.add_edge(START, "extract_texts")
    g.add_edge("extract_texts", "analyze_compliance")
    g.add_conditional_edges(
        "analyze_compliance",
        _route_score,
        {"conforme": "generate_report", "a_valider": "envoie_au_CO"},
    )
    g.add_edge("envoie_au_CO", "generate_report")
    g.add_edge("generate_report", END)

    return g.compile()
