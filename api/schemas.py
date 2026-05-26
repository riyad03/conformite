from __future__ import annotations

from pydantic import BaseModel


class AnalyseRequest(BaseModel):
    procedures: list[str]
    extra_context_docs: list[str] = []
    referentiel_path: str | None = None          # override AppConfig default
    system_prompts: dict[str, str] = {}          # agent_name → prompt override


class ProcedureSummary(BaseModel):
    procedure_name: str
    score_global: int
    niveau_global: str
    nb_concernes: int
    nb_conformes: int
    nb_partiels: int
    nb_non_conformes: int
    resume_executif: str
    rapport_html: str


class AnalyseResponse(BaseModel):
    results: list[ProcedureSummary]
    global_summary: ProcedureSummary | None = None


class ProcedureItem(BaseModel):
    title: str
    filename: str


class FileItem(BaseModel):
    filename: str
    path: str
