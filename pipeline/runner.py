"""Pipeline builder and public run functions."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from module_folder.config import AppConfig
from module_folder.models import RapportFinal
from module_folder.pipeline.nodes import (
    node_analyse_evaluate_all,
    node_extraction_all,
    node_formatter,
    node_rapport_all,
    node_summarizer,
    node_validate_all,
)
from module_folder.pipeline.state import PipelineState


# ── graph factory ─────────────────────────────────────────────────────────────

def build_pipeline():
    g = StateGraph(PipelineState)
    for name, fn in [
        ("extraction_all",       node_extraction_all),
        ("summarizer",           node_summarizer),
        ("formatter",            node_formatter),
        ("validate_all",         node_validate_all),
        ("analyse_evaluate_all", node_analyse_evaluate_all),
        ("rapport_all",          node_rapport_all),
    ]:
        g.add_node(name, fn)

    g.set_entry_point("extraction_all")
    g.add_edge("extraction_all",       "summarizer")
    g.add_edge("summarizer",           "formatter")
    g.add_edge("formatter",            "validate_all")
    g.add_edge("validate_all",         "analyse_evaluate_all")
    g.add_edge("analyse_evaluate_all", "rapport_all")
    g.add_edge("rapport_all",          END)
    return g.compile()


# ── public API ────────────────────────────────────────────────────────────────

def run_batch(
    procedure_paths: list[str],
    selected_processes: list[str] | None = None,
    config: AppConfig | None = None,
    extra_context_docs: list[str] | None = None,
    system_prompts: dict[str, str] | None = None,
    callbacks: list | None = None,
) -> dict[str, RapportFinal]:
    """Run the full pipeline on a batch of procedures. Returns path → RapportFinal."""
    cfg   = config or AppConfig()
    procs = selected_processes or []
    graph_config: dict = {"recursion_limit": 2000}
    if callbacks:
        graph_config["callbacks"] = callbacks

    result = build_pipeline().invoke(
        {
            "procedure_paths":    procedure_paths,
            "referentiel_path":   cfg.referentiel_path,
            "selected_processes": procs,
            "extra_context_docs": extra_context_docs or [],
            "max_eval_iterations": cfg.max_eval_iterations,
            "report_metadata":    cfg.report_metadata,
            "system_prompts":     system_prompts or {},
            "procedure_texts":    {},
            "procedure_summary":  "",
            "extra_context":      "",
            "requirements":       {},
            "validated_req_ids":  {},
            "validation_results": {},
            "analyses":           {},
            "total_eval_iters":   0,
            "rapports":           {},
        },
        config=graph_config,
    )
    return result["rapports"]
