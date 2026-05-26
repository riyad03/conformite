from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from module_folder.api.schemas import AnalyseRequest, AnalyseResponse, ProcedureSummary
from module_folder.config import AppConfig
from module_folder.data.repository import ProcedureResolver
from module_folder.pipeline.runner import run_batch

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_summary(rapport, path: str) -> ProcedureSummary:
    stem = Path(path).stem[:40] if path != "__global__" else "global"
    return ProcedureSummary(
        procedure_name=rapport.procedure_name,
        score_global=rapport.score_global,
        niveau_global=rapport.niveau_global,
        nb_concernes=rapport.nb_concernes,
        nb_conformes=rapport.nb_conformes,
        nb_partiels=rapport.nb_partiels,
        nb_non_conformes=rapport.nb_non_conformes,
        resume_executif=rapport.resume_executif,
        rapport_html=f"rapports/rapport_{stem}.html",
    )


def _resolve(request: AnalyseRequest) -> tuple[AppConfig, list[str]]:
    config = AppConfig()
    if request.referentiel_path:
        config.referentiel_path = request.referentiel_path
    paths = ProcedureResolver(config.procedures_dir).resolve(request.procedures)
    if not paths:
        raise HTTPException(status_code=404, detail="Aucune procédure trouvée pour les titres fournis.")
    return config, paths


def _rapports_to_response(rapports: dict) -> AnalyseResponse:
    results = [
        _to_summary(r, p)
        for p, r in rapports.items()
        if p != "__global__" and r is not None
    ]
    global_r = rapports.get("__global__")
    return AnalyseResponse(
        results=results,
        global_summary=_to_summary(global_r, "__global__") if global_r else None,
    )


# ── blocking endpoint ─────────────────────────────────────────────────────────

@router.post("", response_model=AnalyseResponse)
def analyse(request: AnalyseRequest) -> AnalyseResponse:
    config, paths = _resolve(request)
    rapports = run_batch(
        procedure_paths=paths,
        selected_processes=request.procedures,
        config=config,
        extra_context_docs=request.extra_context_docs,
        system_prompts=request.system_prompts,
    )
    return _rapports_to_response(rapports)


# ── streaming SSE endpoint ────────────────────────────────────────────────────

@router.post("/stream")
async def analyse_stream(request: AnalyseRequest) -> StreamingResponse:
    from module_folder.api.callbacks import StreamingCallback

    loop  = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    _DONE = object()
    cb    = StreamingCallback(queue, loop)

    def _run() -> None:
        from module_folder.pipeline.progress import set_callback, clear_callback
        set_callback(lambda ev: loop.call_soon_threadsafe(queue.put_nowait, ev))
        try:
            config, paths = _resolve_sync(request)
            rapports = run_batch(
                procedure_paths=paths,
                selected_processes=request.procedures,
                config=config,
                extra_context_docs=request.extra_context_docs,
                system_prompts=request.system_prompts,
                callbacks=[cb],
            )
            result = _rapports_to_response(rapports).model_dump()
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "done", "result": result})
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "message": str(exc)})
        finally:
            clear_callback()
            loop.call_soon_threadsafe(queue.put_nowait, _DONE)

    loop.run_in_executor(None, _run)

    async def _stream():
        while True:
            item = await queue.get()
            if item is _DONE:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _resolve_sync(request: AnalyseRequest) -> tuple[AppConfig, list[str]]:
    config = AppConfig()
    if request.referentiel_path:
        config.referentiel_path = request.referentiel_path
    paths = ProcedureResolver(config.procedures_dir).resolve(request.procedures)
    if not paths:
        raise ValueError("Aucune procédure trouvée.")
    return config, paths
