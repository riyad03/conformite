from __future__ import annotations

from pathlib import Path

from .graph import build_agent
from .state import initial_state


def run_batch(
    procedures_dir: str | Path,
    referentiel_path: str | Path,
    ocr_lang: str = "fra+eng",
    score_threshold: int = 80,
) -> list[dict]:
    agent = build_agent()
    proc_dir = Path(procedures_dir)
    proc_files = sorted(proc_dir.glob("*.pdf"))
    print(f"{len(proc_files)} procedures trouvees dans {proc_dir}/")

    resultats = []
    for proc_path in proc_files:
        print(f"\n{'-'*60}")
        print(f"-> {proc_path.name}")
        try:
            result = agent.invoke(
                initial_state(str(proc_path), str(referentiel_path), ocr_lang)
            )
            r = result["rapport"]
            resultats.append({
                "procedure": proc_path.name,
                "score":     r["score_conformite"],
                "niveau":    r["niveau"],
                "ecarts":    len(r.get("ecarts", [])),
                "pdf":       result["rapport_pdf_path"],
                "json":      result["rapport_json_path"],
            })
        except Exception as exc:
            print(f"  [ERR] {exc}")
            resultats.append({
                "procedure": proc_path.name,
                "score": -1,
                "niveau": "Erreur",
                "ecarts": 0,
                "pdf": "",
                "json": "",
            })

    _print_summary(resultats)
    return resultats


def _print_summary(resultats: list[dict]) -> None:
    print(f"\n{'='*70}")
    print(f"{'PROCEDURE':<48} {'SCORE':>6}  {'NIVEAU':<25} {'ECARTS':>6}")
    print("-" * 70)
    for r in resultats:
        score_str = f"{r['score']}%" if r["score"] >= 0 else "Erreur"
        print(f"{r['procedure'][:48]:<48} {score_str:>6}  {r['niveau']:<25} {r['ecarts']:>6}")
    print("=" * 70)

