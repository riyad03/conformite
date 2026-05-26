from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from module_folder.api.routes.analyse    import router as analyse_router
from module_folder.api.routes.procedures import router as procedures_router
from module_folder.api.routes.files      import router as files_router
from module_folder.api.routes.agents     import router as agents_router

_UI_DIR = Path(__file__).parent.parent / "ui"


def create_app() -> FastAPI:
    app = FastAPI(
        title="GRC Conformité API",
        description="Analyse de conformité réglementaire de procédures internes.",
        version="2.0.0",
    )

    app.include_router(analyse_router,    prefix="/analyse",    tags=["analyse"])
    app.include_router(procedures_router, prefix="/procedures", tags=["procedures"])
    app.include_router(files_router,      prefix="/files",      tags=["files"])
    app.include_router(agents_router,     prefix="/agents",     tags=["agents"])

    @app.get("/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def ui() -> str:
        return (_UI_DIR / "index.html").read_text(encoding="utf-8")

    return app
