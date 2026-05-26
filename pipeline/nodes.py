"""LangGraph node functions — batch pipeline.

Each node operates on ALL procedures simultaneously.
The analyse+evaluate step processes ONE requirement at a time
across ALL procedures in parallel.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from module_folder.agents.analyste import analyze_requirement
from module_folder.agents.evaluateur import evaluate_requirement
from module_folder.agents.formatter import format_context
from module_folder.agents.summarizer import summarize_requirements
from module_folder.agents.validateur import run_validateur_one
from module_folder.config import RAPPORTS_DIR
from module_folder.data.repository import ExtraContextLoader, RequirementsRepository
from module_folder.pipeline import progress as _progress
from module_folder.extractor import extract_text
from module_folder.llm import get_llm
from module_folder.models import RapportFinal, RequirementAnalysis
from module_folder.report.html_generator import generate_html
from module_folder.report.validation_report import generate_validation_html


# ── helpers ───────────────────────────────────────────────────────────────────

def _sp(state: dict, agent: str) -> str | None:
    """Return system prompt override for an agent, or None to use default."""
    return (state.get("system_prompts") or {}).get(agent)


# ── node 1: extract all procedures ───────────────────────────────────────────

def node_extraction_all(state: dict) -> dict:
    procedure_paths = state["procedure_paths"]
    print(f"\n{'=' * 60}\nBatch : {len(procedure_paths)} procédure(s)")

    procedure_texts: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(extract_text, p): p for p in procedure_paths}
        for future in as_completed(futures):
            path = futures[future]
            text = future.result()
            procedure_texts[path] = text
            print(f"  -> {Path(path).name}: {len(text):,} car.")

    extra_context = ExtraContextLoader.load(state["extra_context_docs"])
    requirements  = RequirementsRepository(state["referentiel_path"]).load()
    print(f"  -> {len(requirements)} exigences à traiter")

    return {
        "procedure_texts":    procedure_texts,
        "extra_context":      extra_context,
        "requirements":       requirements,
        "procedure_summary":  "",
        "validated_req_ids":  {},
        "validation_results": {},
        "analyses":           {},
        "total_eval_iters":   0,
        "rapports":           {},
    }


# ── node 2: summarize requirements ───────────────────────────────────────────

def node_summarizer(state: dict) -> dict:
    print("  [Summarizer] Résumé du cadre réglementaire...")
    summary = summarize_requirements(
        state["requirements"],
        llm=get_llm(),
        system_prompt=_sp(state, "summarizer"),
    )
    print(f"  [Summarizer] {len(summary)} car.")
    return {"procedure_summary": summary}


# ── node 3: format context ────────────────────────────────────────────────────

def node_formatter(state: dict) -> dict:
    enriched = format_context(
        state["selected_processes"],
        state["procedure_summary"],
        state["extra_context"],
    )
    print(f"  [Formatter] Contexte structuré ({len(enriched)} car.)")
    return {"extra_context": enriched}


# ── node 4: validate all (requirement × procedure, parallel) ─────────────────

def node_validate_all(state: dict) -> dict:
    requirements    = state["requirements"]
    procedure_texts = state["procedure_texts"]
    llm             = get_llm()
    sp              = _sp(state, "validateur")
    total_pairs     = len(requirements) * len(procedure_texts)
    print(f"\n[Validate ALL] {len(requirements)} exigences × {len(procedure_texts)} procédures = {total_pairs} paires (threads)...")

    validation_results: dict[str, dict] = {p: {} for p in procedure_texts}
    validated_req_ids:  dict[str, list] = {p: [] for p in procedure_texts}

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures: dict = {}
        for path, proc_text in procedure_texts.items():
            proc_ctx = proc_text[:6000]
            for req_id, req_text in requirements.items():
                f = pool.submit(
                    run_validateur_one,
                    req_id, req_text, proc_ctx,
                    state["selected_processes"],
                    llm=llm,
                    system_prompt=sp,
                )
                futures[f] = (path, req_id)

        done = 0
        for future in as_completed(futures):
            path, req_id = futures[future]
            result = future.result()
            validation_results[path][req_id] = {
                "req_id":      req_id,
                "req_text":    requirements[req_id],
                "is_relevant": result.is_relevant,
                "reason":      result.reason,
            }
            if result.is_relevant:
                validated_req_ids[path].append(req_id)
            done += 1
            _progress.emit("validate_all", done, total_pairs, req_id)
            if done % 20 == 0 or done == total_pairs:
                print(f"  [{done}/{total_pairs}] validé")

    # save per-procedure validation HTML
    for path, results in validation_results.items():
        _save_validation_report(path, results, state)

    nb_total = sum(len(v) for v in validated_req_ids.values())
    print(f"  [OK] {nb_total} paires (req × proc) retenues")
    return {"validation_results": validation_results, "validated_req_ids": validated_req_ids}


def _save_validation_report(path: str, results: dict, state: dict) -> None:
    out_dir  = RAPPORTS_DIR; out_dir.mkdir(exist_ok=True)
    stem     = Path(path).stem[:40]
    proc_name = Path(path).name
    ordered  = {rid: results[rid] for rid in state["requirements"] if rid in results}
    (out_dir / f"validation_{stem}.json").write_text(
        json.dumps(list(ordered.values()), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    html = generate_validation_html(ordered, proc_name, state["selected_processes"])
    (out_dir / f"validation_{stem}.html").write_text(html, encoding="utf-8")


# ── node 5: analyse + evaluate (ALL req × proc pairs in parallel) ────────────

def node_analyse_evaluate_all(state: dict) -> dict:
    """Analyse and evaluate ALL (requirement, procedure) pairs in parallel threads."""
    requirements    = state["requirements"]
    procedure_texts = state["procedure_texts"]
    validated       = state["validated_req_ids"]   # path → [req_ids]
    max_iters       = state["max_eval_iterations"]
    llm             = get_llm()
    sp_analyste     = _sp(state, "analyste")
    sp_evaluateur   = _sp(state, "evaluateur")

    # build flat list of (req_id, path) pairs that passed validation
    pairs = [
        (req_id, path)
        for path in procedure_texts
        for req_id in validated.get(path, [])
    ]
    total = len(pairs)
    print(f"\n[Analyse+Evaluate] {total} paires (req × proc) en parallèle (threads)...")

    analyses:   dict[str, list[RequirementAnalysis]] = {p: [] for p in procedure_texts}
    total_iters = 0
    done        = 0

    def _run_one(req_id: str, path: str) -> tuple[str, str, RequirementAnalysis, int]:
        req_text  = requirements[req_id]
        proc_text = procedure_texts[path]
        critiques: list[str] = []
        for iteration in range(max_iters):
            extra = state["extra_context"]
            if critiques:
                extra += "\n\n" + "\n\n".join(f"CRITIQUE #{j+1}:\n{c}" for j, c in enumerate(critiques))
            analysis = analyze_requirement(
                req_id, req_text, proc_text, extra,
                llm=llm, system_prompt=sp_analyste,
            )
            feedback = evaluate_requirement(
                analysis, proc_text, extra,
                llm=llm, system_prompt=sp_evaluateur,
            )
            if feedback.satisfait or not feedback.should_reanalyse:
                return req_id, path, analysis, iteration + 1
            critiques.append(feedback.critique)
        return req_id, path, analysis, max_iters

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_run_one, req_id, path): (req_id, path) for req_id, path in pairs}
        for future in as_completed(futures):
            req_id, path        = futures[future]
            _, _, analysis, n   = future.result()
            analysis.procedure_name = Path(path).name
            analyses[path].append(analysis)
            total_iters += n
            done        += 1
            _progress.emit("analyse_evaluate_all", done, total, req_id)
            print(f"  [{done}/{total}] {req_id} ({Path(path).stem[:20]}): {analysis.compliance_level}")

    return {"analyses": analyses, "total_eval_iters": total_iters}


# ── node 6: build all reports ─────────────────────────────────────────────────

def node_rapport_all(state: dict) -> dict:
    print("\n[RAPPORT] Construction des rapports...")
    rapports: dict[str, RapportFinal] = {}
    llm = get_llm()

    for path, path_analyses in state["analyses"].items():
        if not path_analyses:
            continue
        rapport = _build_rapport(path, path_analyses, state, llm)
        rapports[path] = rapport
        _save_rapport(rapport, path)

    # global report when multiple procedures
    if len(rapports) > 1:
        global_rapport = _build_global(rapports, state, llm)
        _save_global_rapport(global_rapport)
        rapports["__global__"] = global_rapport

    return {"rapports": rapports}


def _build_rapport(path: str, analyses: list[RequirementAnalysis], state: dict, llm) -> RapportFinal:
    proc_name = Path(path).name
    nb_co = sum(1 for a in analyses if a.compliance_level == "Conforme")
    nb_pc = sum(1 for a in analyses if a.compliance_level == "Partiellement conforme")
    nb_nc = sum(1 for a in analyses if a.compliance_level == "Non conforme")
    score  = int((nb_co + 0.5 * nb_pc) / max(len(analyses), 1) * 100)
    niveau = "Conforme" if score >= 85 else "Partiellement conforme" if score >= 50 else "Non conforme"
    meta   = state["report_metadata"]

    resume = llm.invoke([
        SystemMessage(content="Tu es expert GRC. Redige un resume executif 3-4 phrases en francais. Texte brut uniquement."),
        HumanMessage(content=f"Procedure: {proc_name}\nScore: {score}/100 ({niveau})\nConformes: {nb_co} | Partiels: {nb_pc} | NC: {nb_nc}"),
    ]).content.strip()

    return RapportFinal(
        procedure_name=proc_name,
        selected_processes=state["selected_processes"],
        score_global=score, niveau_global=niveau, resume_executif=resume,
        nb_total=len(state["requirements"]), nb_concernes=len(analyses),
        nb_conformes=nb_co, nb_partiels=nb_pc, nb_non_conformes=nb_nc,
        nb_iterations_evaluateur=state["total_eval_iters"],
        analyses=analyses,
        **{k: meta.get(k, "") for k in ["client","autorite_emettrice","reference","intitule","entree_en_vigueur","echeance_conformite","date_publication"]},
    )


def _build_global(rapports: dict[str, RapportFinal], state: dict, llm) -> RapportFinal:
    valid = [(Path(p).name, r) for p, r in rapports.items() if p != "__global__"]
    all_analyses = [a for _, r in valid for a in r.analyses]
    nb_co  = sum(1 for a in all_analyses if a.compliance_level == "Conforme")
    nb_pc  = sum(1 for a in all_analyses if a.compliance_level == "Partiellement conforme")
    nb_nc  = sum(1 for a in all_analyses if a.compliance_level == "Non conforme")
    score  = int((nb_co + 0.5 * nb_pc) / max(len(all_analyses), 1) * 100)
    niveau = "Conforme" if score >= 85 else "Partiellement conforme" if score >= 50 else "Non conforme"
    meta   = state["report_metadata"]
    names  = [n for n, _ in valid]

    # per-procedure summary for the LLM
    proc_lines = "\n".join(
        f"- {name}: {r.score_global}/100 ({r.niveau_global})"
        f" — {r.nb_conformes} conf. / {r.nb_partiels} part. / {r.nb_non_conformes} NC"
        for name, r in valid
    )

    # requirements non-compliant across multiple procedures
    from collections import Counter
    nc_counts = Counter(
        a.requirement_id
        for a in all_analyses if a.compliance_level != "Conforme"
    )
    common_nc = "\n".join(
        f"- {rid} ({cnt}/{len(valid)} proc.)"
        for rid, cnt in nc_counts.most_common(5)
    ) or "Aucune."

    resume = llm.invoke([
        SystemMessage(content=(
            "Tu es expert GRC senior. Redige un résumé exécutif global de 4-6 phrases en français "
            "synthétisant la conformité de l'ensemble des procédures : score unifié, procédures les "
            "plus critiques, exigences transversales non conformes et priorités d'action collectives. "
            "Texte brut uniquement, sans titre ni markdown."
        )),
        HumanMessage(content=(
            f"Score unifié : {score}/100 ({niveau})\n"
            f"Total : {len(all_analyses)} analyses (conformes: {nb_co}, partiels: {nb_pc}, NC: {nb_nc})\n\n"
            f"Résultats par procédure :\n{proc_lines}\n\n"
            f"Exigences transversales non conformes :\n{common_nc}"
        )),
    ]).content.strip()

    return RapportFinal(
        procedure_name=f"Rapport Global — {len(valid)} procédure(s)",
        selected_processes=names,
        score_global=score, niveau_global=niveau, resume_executif=resume,
        nb_total=sum(r.nb_total for _, r in valid),
        nb_concernes=len(all_analyses),
        nb_conformes=nb_co, nb_partiels=nb_pc, nb_non_conformes=nb_nc,
        nb_iterations_evaluateur=sum(r.nb_iterations_evaluateur for _, r in valid),
        analyses=all_analyses,
        **{k: meta.get(k, "") for k in ["client","autorite_emettrice","reference","intitule","entree_en_vigueur","echeance_conformite","date_publication"]},
    )


def _save_rapport(rapport: RapportFinal, path: str) -> None:
    out_dir = RAPPORTS_DIR; out_dir.mkdir(exist_ok=True)
    stem    = Path(path).stem[:40]
    html    = generate_html(rapport)
    (out_dir / f"rapport_{stem}.html").write_text(html, encoding="utf-8")
    (out_dir / f"rapport_{stem}.json").write_text(rapport.model_dump_json(indent=2), encoding="utf-8")
    print(f"  [OK] rapport_{stem}.html")
    try:
        from weasyprint import HTML as W
        W(string=html).write_pdf(str(out_dir / f"rapport_{stem}.pdf"))
    except Exception as exc:
        print(f"  [WARN] PDF: {exc}")


def _save_global_rapport(rapport: RapportFinal) -> None:
    out_dir = RAPPORTS_DIR; out_dir.mkdir(exist_ok=True)
    html    = generate_html(rapport)
    (out_dir / "rapport_global.html").write_text(html, encoding="utf-8")
    (out_dir / "rapport_global.json").write_text(rapport.model_dump_json(indent=2), encoding="utf-8")
    print(f"  [OK] rapport_global.html — score: {rapport.score_global}/100")
    try:
        from weasyprint import HTML as W
        W(string=html).write_pdf(str(out_dir / "rapport_global.pdf"))
    except Exception as exc:
        print(f"  [WARN] PDF: {exc}")
