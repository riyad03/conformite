from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .extractor import _suivie
from .state import ConformiteState

_COULEUR_NIVEAU = {"Conforme": "#27ae60", "Partiellement conforme": "#f39c12", "Non conforme": "#e74c3c"}
_COULEUR_IMPACT = {"Critique": "#e74c3c", "Majeur": "#f39c12", "Mineur": "#3498db"}
_COULEUR_RISQUE = {"Élevé": "#e74c3c", "Moyen": "#f39c12", "Faible": "#27ae60"}


def _badge(texte: str, couleur: str) -> str:
    return (
        f'<span style="background:{couleur};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:.85em;font-weight:bold">{texte}</span>'
    )


def _tr_ecart(e: dict) -> str:
    imp = e.get("impact", "")
    return (
        f'<tr>'
        f'<td style="padding:8px;border:1px solid #ddd">{e.get("id","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{e.get("exigence_manquante","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{e.get("description_ecart","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd;text-align:center">'
        f'{_badge(imp, _COULEUR_IMPACT.get(imp, "#7f8c8d"))}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{e.get("risque","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{e.get("recommandation","")}</td>'
        f'</tr>'
    )


def _tr_risque(rg: dict) -> str:
    niv = rg.get("niveau", "")
    return (
        f'<tr>'
        f'<td style="padding:8px;border:1px solid #ddd">{rg.get("categorie","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{rg.get("description","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd;text-align:center">'
        f'{_badge(niv, _COULEUR_RISQUE.get(niv, "#7f8c8d"))}</td>'
        f'</tr>'
    )


def _tr_action(a: dict) -> str:
    return (
        f'<tr>'
        f'<td style="padding:8px;border:1px solid #ddd;text-align:center;font-weight:bold">'
        f'{a.get("priorite","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{a.get("action","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{a.get("echeance","")}</td>'
        f'<td style="padding:8px;border:1px solid #ddd">{a.get("responsable","")}</td>'
        f'</tr>'
    )


def build_html(r: dict, proc_path: str, ref_path: str) -> str:
    score  = r["score_conformite"]
    niveau = r["niveau"]
    c      = _COULEUR_NIVEAU.get(niveau, "#7f8c8d")
    date   = datetime.now().strftime("%d/%m/%Y %H:%M")

    jauge = (
        f'<div style="margin:16px 0">'
        f'<div style="background:#ecf0f1;border-radius:8px;height:28px;overflow:hidden">'
        f'<div style="width:{score}%;background:{c};height:100%;display:flex;'
        f'align-items:center;justify-content:center;color:#fff;font-weight:bold">'
        f'{score}%</div></div></div>'
    )

    ecarts  = r.get("ecarts", [])
    risques = r.get("risques_globaux", [])
    plan    = r.get("plan_action", [])

    ecarts_html = (
        '<table><thead><tr>'
        '<th>Réf.</th><th>Exigence</th><th>Écart</th>'
        '<th>Impact</th><th>Risque</th><th>Recommandation</th>'
        '</tr></thead><tbody>'
        + "".join(_tr_ecart(e) for e in ecarts)
        + '</tbody></table>'
    ) if ecarts else '<p style="color:#27ae60">Aucun écart détecté.</p>'

    risques_html = (
        '<table><thead><tr><th>Catégorie</th><th>Description</th><th>Niveau</th></tr></thead><tbody>'
        + "".join(_tr_risque(rg) for rg in risques)
        + '</tbody></table>'
    ) if risques else '<p>Aucun risque identifié.</p>'

    plan_html = (
        '<table><thead><tr><th>#</th><th>Action</th><th>Échéance</th><th>Responsable</th></tr></thead><tbody>'
        + "".join(_tr_action(a) for a in plan)
        + '</tbody></table>'
    ) if plan else '<p>Aucune action requise.</p>'

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Rapport de Conformité</title>
<style>
  body{{font-family:Arial,sans-serif;max-width:1100px;margin:0 auto;padding:24px;color:#2c3e50}}
  h1{{color:{c}}}
  h2{{color:#2c3e50;border-bottom:2px solid {c};padding-bottom:4px;margin-top:32px}}
  table{{border-collapse:collapse;width:100%;margin-top:12px;font-size:.9em}}
  th{{background:#2c3e50;color:#fff;padding:10px 8px;text-align:left}}
  tr:nth-child(even){{background:#f8f9fa}}
  .meta{{color:#7f8c8d;font-size:.9em}}
  .resume-box{{background:#f0f4f8;border-left:4px solid {c};padding:12px 16px;border-radius:4px}}
  .search-wrap{{display:flex;align-items:center;gap:10px;margin:20px 0 8px}}
  .search-wrap input{{flex:1;padding:9px 14px 9px 36px;border:1px solid #ccc;border-radius:6px;
    font-size:.95em;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E") no-repeat 10px center}}
  .search-wrap input:focus{{outline:none;border-color:{c};box-shadow:0 0 0 2px {c}33}}
  tr.hidden{{display:none}}
</style>
<script>
function filterTables(){{
  var q=document.getElementById("searchInput").value.toLowerCase();
  var n=0;
  document.querySelectorAll("tbody tr").forEach(function(tr){{
    var show=!q||tr.textContent.toLowerCase().includes(q);
    tr.classList.toggle("hidden",!show);
    if(show)n++;
  }});
  document.getElementById("searchCount").textContent=q?"("+n+" ligne"+(n>1?"s":"")+")":"";
}}
</script>
</head><body>
<h1>Rapport d'Analyse de Conformité</h1>
<p class="meta">Généré le <strong>{date}</strong> &nbsp;|&nbsp;
  Procédure : <code>{proc_path}</code> &nbsp;|&nbsp; Référentiel : <code>{ref_path}</code></p>
<div class="search-wrap">
  <input id="searchInput" type="text" placeholder="Rechercher dans les tableaux…" oninput="filterTables()">
  <span id="searchCount"></span>
</div>
<h2>Score de Conformité Globale</h2>
<p>Niveau : {_badge(niveau, c)}</p>{jauge}
<h2>Résumé Exécutif</h2>
<div class="resume-box">{r.get("resume", "")}</div>
<h2>Écarts Détectés ({len(ecarts)})</h2>{ecarts_html}
<h2>Risques Globaux</h2>{risques_html}
<h2>Plan d'Action</h2>{plan_html}
</body></html>"""


def generate_report(state: ConformiteState) -> dict:
    from weasyprint import HTML as WeasyprintHTML

    output_dir = Path("rapports")
    output_dir.mkdir(exist_ok=True)
    stem = Path(state["procedure_path"]).stem[:40]

    html      = build_html(state["rapport"], state["procedure_path"], state["referentiel_path"])
    html_path = output_dir / f"rapport_{stem}.html"
    pdf_path  = output_dir / f"rapport_{stem}.pdf"
    json_path = output_dir / f"rapport_{stem}.json"

    html_path.write_text(html, encoding="utf-8")
    WeasyprintHTML(string=html).write_pdf(str(pdf_path))
    json_path.write_text(json.dumps(state["rapport"], ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] PDF  : {pdf_path}")
    print(f"[OK] JSON : {json_path}")

    log = list(state.get("suivie_log", [])) + [
        _suivie("report_generated", {"pdf": str(pdf_path), "json": str(json_path)})
    ]
    return {
        "rapport_html_path": str(html_path),
        "rapport_pdf_path":  str(pdf_path),
        "rapport_json_path": str(json_path),
        "suivie_log":        log,
    }
