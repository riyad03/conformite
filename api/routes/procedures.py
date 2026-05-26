from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from module_folder.api.schemas import ProcedureItem
from module_folder.config import AppConfig

router = APIRouter()


@router.get("", response_model=list[ProcedureItem])
def list_procedures() -> list[ProcedureItem]:
    config = AppConfig()
    base   = Path(config.procedures_dir)
    if not base.exists():
        return []
    return [
        ProcedureItem(title=p.stem, filename=p.name)
        for p in sorted(base.glob("*.pdf"))
    ]


@router.post("/upload", response_model=ProcedureItem)
async def upload_procedure(file: UploadFile = File(...)) -> ProcedureItem:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    config  = AppConfig()
    dest_dir = Path(config.procedures_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    return ProcedureItem(title=dest.stem, filename=dest.name)
