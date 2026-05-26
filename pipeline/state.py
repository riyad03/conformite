from __future__ import annotations

from typing import TypedDict

from module_folder.models import RequirementAnalysis, RapportFinal


class PipelineState(TypedDict):
    # ── inputs ────────────────────────────────────────────────────────────────
    procedure_paths: list[str]                        # all procedures in the batch
    referentiel_path: str
    selected_processes: list[str]
    extra_context_docs: list[str]
    max_eval_iterations: int
    report_metadata: dict
    system_prompts: dict[str, str]                    # agent_name → prompt override

    # ── populated during execution ────────────────────────────────────────────
    procedure_texts: dict[str, str]                   # path → extracted text
    procedure_summary: str                            # requirements framework summary
    extra_context: str                                # formatted context string
    requirements: dict[str, str]                      # req_id → text

    # per-procedure validation
    validated_req_ids: dict[str, list[str]]           # path → [req_ids]
    validation_results: dict[str, dict]               # path → {req_id: result_dict}

    # per-procedure analyses
    analyses: dict[str, list[RequirementAnalysis]]    # path → [RequirementAnalysis]
    total_eval_iters: int

    # final reports (path → rapport, "__global__" → global)
    rapports: dict[str, RapportFinal]
