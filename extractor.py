from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from .state import ConformiteState


def _suivie(event: str, details: dict) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent":     "conformite",
        "event":     event,
        "details":   details,
    }


def extract_text(source: str | Path, lang: str = "fra+eng") -> str:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    suffix = path.suffix.lower()

    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")

    if suffix == ".xlsx":
        df = pd.read_excel(path)
        lines = []
        for _, row in df.iterrows():
            art   = str(row.get("source_passage") or "")
            title = str(row.get("title")          or "")
            desc  = str(row.get("description")    or "")
            if title or desc:
                lines.append(f"[{art}] {title}\n{desc}")
        return "\n---\n".join(lines)

    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        native_text = "\n\n".join(pages).strip()
        avg_chars = len(native_text) / max(len(pages), 1)
        if avg_chars < 100:
            print(f"  [OCR] PDF scanne ({avg_chars:.0f} car/page)")
            images = convert_from_path(path, dpi=300)
            return "\n\n".join(
                pytesseract.image_to_string(img, lang=lang) for img in images
            ).strip()
        return native_text

    if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"):
        return pytesseract.image_to_string(Image.open(path), lang=lang).strip()

    raise ValueError(f"Format non supporté : {suffix}")


def extract_texts(state: ConformiteState) -> dict:
    lang = state.get("ocr_lang", "fra+eng")

    print("Extraction de la procedure...")
    texte_procedure = extract_text(state["procedure_path"], lang=lang)
    print(f"  -> {len(texte_procedure):,} caracteres")

    print("Extraction du referentiel...")
    texte_referentiel = extract_text(state["referentiel_path"], lang=lang)
    print(f"  -> {len(texte_referentiel):,} caracteres")

    log = list(state.get("suivie_log", [])) + [
        _suivie("texts_extracted", {
            "procedure_chars":   str(len(texte_procedure)),
            "referentiel_chars": str(len(texte_referentiel)),
        })
    ]
    return {
        "texte_procedure":   texte_procedure,
        "texte_referentiel": texte_referentiel,
        "suivie_log":        log,
    }
