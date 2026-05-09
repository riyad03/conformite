from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class ConformiteState(TypedDict):
    procedure_path:    str
    referentiel_path:  str
    ocr_lang:          str
    texte_procedure:   str
    texte_referentiel: str
    rapport:           dict[str, Any]
    rapport_html_path: str
    rapport_pdf_path:  str
    rapport_json_path: str
    score_conformite:  int
    niveau:            str
    suivie_log:        list[dict[str, Any]]
    error:             Optional[str]


def initial_state(procedure_path: str, referentiel_path: str, ocr_lang: str = "fra+eng") -> ConformiteState:
    return ConformiteState(
        procedure_path=procedure_path,
        referentiel_path=referentiel_path,
        ocr_lang=ocr_lang,
        texte_procedure="",
        texte_referentiel="",
        rapport={},
        rapport_html_path="",
        rapport_pdf_path="",
        rapport_json_path="",
        score_conformite=0,
        niveau="",
        suivie_log=[],
        error=None,
    )
