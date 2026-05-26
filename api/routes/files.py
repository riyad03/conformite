"""Endpoints for uploading referentiel files and extra context documents."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from module_folder.api.schemas import FileItem
from module_folder.config import PROJECT_ROOT

router = APIRouter()

_REFERENTIELS_DIR = PROJECT_ROOT / "referentiels"
_CONTEXT_DIR      = PROJECT_ROOT / "context_docs"


@router.get("/referentiels", response_model=list[FileItem])
def list_referentiels() -> list[FileItem]:
    _REFERENTIELS_DIR.mkdir(exist_ok=True)
    files = sorted(_REFERENTIELS_DIR.glob("*.xlsx")) + sorted(_REFERENTIELS_DIR.glob("*.xls"))
    return [FileItem(filename=f.name, path=str(f)) for f in files]


@router.post("/referentiels/upload", response_model=FileItem)
async def upload_referentiel(file: UploadFile = File(...)) -> FileItem:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Seuls les fichiers Excel (.xlsx/.xls) sont acceptés.")
    _REFERENTIELS_DIR.mkdir(exist_ok=True)
    dest = _REFERENTIELS_DIR / file.filename
    dest.write_bytes(await file.read())
    return FileItem(filename=dest.name, path=str(dest))


@router.get("/context", response_model=list[FileItem])
def list_context_docs() -> list[FileItem]:
    _CONTEXT_DIR.mkdir(exist_ok=True)
    return [FileItem(filename=f.name, path=str(f)) for f in sorted(_CONTEXT_DIR.iterdir()) if f.is_file()]


@router.post("/context/upload", response_model=FileItem)
async def upload_context_doc(file: UploadFile = File(...)) -> FileItem:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis.")
    _CONTEXT_DIR.mkdir(exist_ok=True)
    dest = _CONTEXT_DIR / file.filename
    dest.write_bytes(await file.read())
    return FileItem(filename=dest.name, path=str(dest))
