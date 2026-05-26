from __future__ import annotations

from pathlib import Path

import pandas as pd

from module_folder.extractor import extract_text


class RequirementsRepository:
    """Loads regulatory requirements from an Excel referentiel (SRP: data access only)."""

    def __init__(self, path: str) -> None:
        self._path = path

    def load(self) -> dict[str, str]:
        df = pd.read_excel(self._path)
        reqs: dict[str, str] = {}
        for _, row in df.iterrows():
            req_id = str(row.get("source_passage") or "").strip()
            title  = str(row.get("title")          or "").strip()
            desc   = str(row.get("description")    or "").strip()
            if req_id and (title or desc):
                reqs[req_id] = f"{title}\n{desc}".strip()
        return reqs


class ProcedureResolver:
    """Resolves procedure titles to their PDF paths (SRP: file resolution only)."""

    def __init__(self, procedures_dir: str) -> None:
        self._dir = Path(procedures_dir)

    def resolve(self, titles: list[str]) -> list[str]:
        paths: list[str] = []
        for title in titles:
            path = self._resolve_one(title)
            if path:
                paths.append(path)
        return paths

    def _resolve_one(self, title: str) -> str | None:
        exact = self._dir / f"{title}.pdf"
        if exact.exists():
            print(f"  [+] '{title}' -> {exact.name}")
            return str(exact)

        candidates = list(self._dir.glob("*.pdf"))
        found = [p for p in candidates
                 if title.lower() in p.stem.lower() or p.stem.lower() in title.lower()]
        if not found:
            print(f"  [WARN] Aucune procedure trouvee pour : '{title}'")
            return None
        if len(found) > 1:
            print(f"  [WARN] Plusieurs correspondances pour '{title}', utilisation de : {found[0].name}")
        else:
            print(f"  [+] '{title}' -> {found[0].name}")
        return str(found[0])


class ExtraContextLoader:
    """Loads supplementary context documents (SRP: optional doc loading only)."""

    @staticmethod
    def load(doc_paths: list[str]) -> str:
        parts: list[str] = []
        for p in doc_paths:
            try:
                parts.append(extract_text(p))
                print(f"  [+] Contexte charge: {p}")
            except Exception as exc:
                print(f"  [WARN] {p}: {exc}")
        return "\n\n".join(parts)
