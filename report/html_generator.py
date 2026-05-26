from __future__ import annotations

import math
import re
from datetime import datetime

from module_folder.models import RapportFinal, RequirementAnalysis

# ── palette ──────────────────────────────────────────────────────────────────
_RED  = "#c0392b"
_DARK = "#1a1a1a"

_C_LEV  = {"Conforme": "#27ae60", "Partiellement conforme": "#f39c12", "Non conforme": "#e74c3c"}
_C_CRIT = {"Critique": "#e74c3c", "Majeur": "#f39c12", "Mineur": "#3498db", "N/A": "#95a5a6"}
_C_PRIO = {
    "P1 - Urgente":   "#e74c3c",
    "P2 - Haute":     "#e67e22",
    "P3 - Modérée":   "#f39c12",
    "P4 - Surveiller": "#27ae60",
}


# ── micro helpers ─────────────────────────────────────────────────────────────

def _badge(text: str, color: str, small: bool = False) -> str:
    fs = ".75em" if small else ".82em"
    return (
        f"<span style='background:{color};color:#fff;padding:2px 8px;border-radius:4px;"
        f"font-size:{fs};font-weight:bold;white-space:nowrap'>{text}</span>"
    )


def _trunc(text: str, n: int) -> str:
    text = (text or "").strip()
    return text[:n] + "…" if len(text) > n else text


def _first_words(text: str, n: int = 3) -> str:
    words = (text or "").split()
    return text if len(words) <= n else " ".join(words[:n]) + "…"


def _md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.DOTALL)
    return re.sub(r"\*([^*\n]+?)\*", r"<em>\1</em>", text)


def _donut_svg(nc: int, pc: int, co: int) -> str:
    total = nc + pc + co
    if total == 0:
        return ""
    cx, cy, ro, ri = 100, 100, 75, 45

    def seg(p0: float, p1: float, color: str) -> str:
        if p1 - p0 < 0.001:
            return ""
        a0 = p0 * 2 * math.pi - math.pi / 2
        a1 = p1 * 2 * math.pi - math.pi / 2
        lg = 1 if (p1 - p0) > 0.5 else 0
        x0o, y0o = cx + ro * math.cos(a0), cy + ro * math.sin(a0)
        x1o, y1o = cx + ro * math.cos(a1), cy + ro * math.sin(a1)
        x1i, y1i = cx + ri * math.cos(a1), cy + ri * math.sin(a1)
        x0i, y0i = cx + ri * math.cos(a0), cy + ri * math.sin(a0)
        return (
            f'<path fill="{color}" d="M{x0o:.1f},{y0o:.1f} A{ro},{ro} 0 {lg},1 {x1o:.1f},{y1o:.1f}'
            f' L{x1i:.1f},{y1i:.1f} A{ri},{ri} 0 {lg},0 {x0i:.1f},{y0i:.1f}Z"/>'
        )

    p_nc, p_pc = nc / total, pc / total
    paths = (
        seg(0, p_nc, "#e74c3c")
        + seg(p_nc, p_nc + p_pc, "#f39c12")
        + seg(p_nc + p_pc, 1.0, "#27ae60")
    )
    legend = (
        '<rect x="0" y="2" width="12" height="12" fill="#27ae60"/>'
        f'<text x="16" y="13" font-size="12" font-family="Arial">Conforme ({co})</text>'
        '<rect x="0" y="22" width="12" height="12" fill="#f39c12"/>'
        f'<text x="16" y="33" font-size="12" font-family="Arial">Partiellement conforme ({pc})</text>'
        '<rect x="0" y="42" width="12" height="12" fill="#e74c3c"/>'
        f'<text x="16" y="53" font-size="12" font-family="Arial">Non conforme ({nc})</text>'
    )
    return (
        "<div style='display:flex;align-items:center;gap:40px;justify-content:center;margin:24px 0'>"
        f'<svg viewBox="0 0 200 200" width="190" height="190">{paths}</svg>'
        f'<svg viewBox="0 0 200 62" width="220" height="62">{legend}</svg></div>'
    )


# ── section builders ──────────────────────────────────────────────────────────

def _cover(r: RapportFinal) -> str:
    date = datetime.now().strftime("%d/%m/%Y")
    meta_rows = "".join(
        f"<tr><td style='background:{_DARK};color:#fff;font-weight:bold;padding:10px 14px;"
        f"white-space:nowrap;width:1%;vertical-align:top'>{k}</td>"
        f"<td style='border:1px solid #ddd;padding:10px 14px'>{v}</td></tr>"
        for k, v in [
            ("CLIENT", r.client),
            ("DATE DE L'ETUDE", date),
            ("AUTORITE", r.autorite_emettrice),
            ("REFERENCE", r.reference),
            ("EN VIGUEUR", r.entree_en_vigueur),
            ("ECHEANCE CONFORMITE", r.echeance_conformite),
            ("VERSION", "V1.0"),
        ]
    )
    return (
        f"<div style='background:#fff;page-break-after:always;break-after:page;padding:0;margin-bottom:40px'>"
        f"<div style='background:{_RED};padding:32px 40px 24px'>"
        f"<div style='color:#fff;font-weight:900;font-size:1.1em;letter-spacing:2px'>BFS CONSULTING</div>"
        f"<div style='color:#ffcccc;font-size:.8em'>Governance &bull; Risk &bull; Compliance</div></div>"
        f"<div style='padding:60px 40px 32px'>"
        f"<h1 style='font-size:3em;font-weight:900;color:{_DARK};line-height:1.1;margin:0 0 16px'>ETUDE D'IMPACT REGLEMENTAIRE</h1>"
        f"<div style='font-size:1.1em;color:{_DARK};margin-bottom:4px'>{r.intitule}</div>"
        f"<div style='font-style:italic;color:#666'>{r.reference}</div></div>"
        f"<div style='padding:0 40px 40px'>"
        f"<table style='width:100%;border-collapse:collapse;font-size:.92em'>{meta_rows}</table></div></div>"
    )


def _synthese(r: RapportFinal) -> str:
    c_glob  = _C_LEV.get(r.niveau_global, "#7f8c8d")
    nb_crit = sum(1 for a in r.analyses if a.criticite in ("Critique", "Majeur") and a.compliance_level != "Conforme")
    nb_p1   = sum(1 for a in r.analyses if a.priorite == "P1 - Urgente")
    gauge = (
        f'<div style="background:#ecf0f1;border-radius:6px;height:26px;overflow:hidden;margin:8px 0 0">'
        f'<div style="width:{r.score_global}%;background:{c_glob};height:100%;display:flex;'
        f'align-items:center;justify-content:center;color:#fff;font-weight:bold;font-size:.9em">'
        f"{r.score_global}%</div></div>"
    )
    indicators = "".join(
        f'<div style="flex:1;min-width:150px;background:{bg};border-radius:8px;padding:14px 12px;text-align:center">'
        f'<div style="font-size:2em;font-weight:900;color:{fc}">{n}</div>'
        f'<div style="font-size:.8em;color:#555;margin-top:3px;line-height:1.3">{label}</div></div>'
        for n, label, bg, fc in [
            (r.nb_conformes,     "Conformes",           "#eafaf1", "#27ae60"),
            (r.nb_partiels,      "Partiellement conf.", "#fef9e7", "#f39c12"),
            (r.nb_non_conformes, "Non conformes",       "#fdedec", "#e74c3c"),
            (nb_crit,            "Critiques en ecart",  "#f4ecf7", "#8e44ad"),
        ]
    )
    msgs = (
        f'<div style="background:#fef5e7;border-left:4px solid #e67e22;padding:12px 16px;'
        f'border-radius:4px;margin-bottom:12px"><strong>Actions urgentes (P1) : {nb_p1}</strong></div>'
        if nb_p1 else ""
    )
    procs_html = ""
    if len(r.selected_processes) > 1:
        # per-procedure score cards
        from collections import defaultdict
        per_proc: dict[str, list] = defaultdict(list)
        for a in r.analyses:
            if a.procedure_name:
                per_proc[a.procedure_name].append(a)
        cards = ""
        for pname, panalyses in per_proc.items():
            pco = sum(1 for a in panalyses if a.compliance_level == "Conforme")
            ppc = sum(1 for a in panalyses if a.compliance_level == "Partiellement conforme")
            pnc = sum(1 for a in panalyses if a.compliance_level == "Non conforme")
            ps  = int((pco + 0.5 * ppc) / max(len(panalyses), 1) * 100)
            pc  = _C_LEV.get(
                "Conforme" if ps >= 85 else "Partiellement conforme" if ps >= 50 else "Non conforme",
                "#7f8c8d",
            )
            cards += (
                f'<div style="flex:1;min-width:180px;border:1px solid {pc}44;border-radius:8px;'
                f'padding:10px 14px;background:{pc}09">'
                f'<div style="font-size:.78em;font-weight:bold;color:#555;margin-bottom:4px;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{pname}">'
                f'{_trunc(pname, 35)}</div>'
                f'<div style="font-size:1.5em;font-weight:900;color:{pc}">{ps}%</div>'
                f'<div style="font-size:.72em;color:#888">'
                f'{pco} conf. &nbsp;·&nbsp; {ppc} part. &nbsp;·&nbsp; {pnc} NC</div>'
                f'<div style="background:#ecf0f1;border-radius:4px;height:6px;margin-top:6px;overflow:hidden">'
                f'<div style="width:{ps}%;height:100%;background:{pc}"></div></div>'
                f'</div>'
            )
        procs_html = (
            f'<div style="margin-top:20px">'
            f'<div style="font-size:.82em;font-weight:bold;color:#555;margin-bottom:8px">Score par procédure</div>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap">{cards}</div>'
            f'</div>'
        )
    return (
        f'<div style="margin-bottom:40px">'
        f'<h2 style="color:{_RED};border-left:5px solid {_RED};padding-left:12px">&#9632; 2. Synthese executive</h2>'
        f'<div style="display:flex;align-items:center;gap:20px;background:#f8f9fa;border-radius:8px;'
        f'padding:20px;margin:20px 0;flex-wrap:wrap">'
        f'<div style="font-size:3.2em;font-weight:900;color:{c_glob};flex-shrink:0">{r.score_global}%</div>'
        f'<div style="flex:1;min-width:200px"><div style="font-weight:bold">Taux de conformite global'
        f' &mdash; {r.niveau_global}</div>{gauge}{procs_html}</div></div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px">{indicators}</div>'
        f"{_donut_svg(r.nb_non_conformes, r.nb_partiels, r.nb_conformes)}{msgs}"
        f'<div style="background:#f0f4f8;border-left:4px solid {c_glob};padding:14px 18px;'
        f'border-radius:4px;line-height:1.7">{r.resume_executif}</div></div>'
    )


def _top5_critiques(r: RapportFinal) -> str:
    def _sort_key(a: RequirementAnalysis) -> int:
        crit = {"Critique": 4, "Majeur": 3, "Mineur": 1, "N/A": 0}
        lev  = {"Non conforme": 3, "Partiellement conforme": 2, "Conforme": 0}
        return crit.get(a.criticite, 0) * 10 + lev.get(a.compliance_level, 0)

    non_conformes = [a for a in r.analyses if a.compliance_level != "Conforme"]

    # for global reports: deduplicate by requirement_id, keep worst-case analysis
    if len(r.selected_processes) > 1:
        seen: dict[str, RequirementAnalysis] = {}
        for a in non_conformes:
            if a.requirement_id not in seen or _sort_key(a) > _sort_key(seen[a.requirement_id]):
                seen[a.requirement_id] = a
        non_conformes = list(seen.values())

    top5 = sorted(non_conformes, key=_sort_key, reverse=True)[:5]

    if not top5:
        return (
            f'<div style="margin-bottom:40px">'
            f'<h2 style="color:{_RED};border-left:5px solid {_RED};padding-left:12px">&#9632; 3. Top 5 Exigences Critiques</h2>'
            f'<p style="color:#27ae60;padding:16px;background:#eafaf1;border-radius:6px">Aucune exigence critique identifiee.</p></div>'
        )

    cards = ""
    for i, a in enumerate(top5, 1):
        c_lev  = _C_LEV.get(a.compliance_level, "#7f8c8d")
        c_crit = _C_CRIT.get(a.criticite, "#95a5a6")
        c_prio = _C_PRIO.get(a.priorite, "#95a5a6")
        proc_tag = (
            f'<span style="font-size:.72em;color:#888;font-weight:normal;margin-left:6px">— {a.procedure_name}</span>'
            if a.procedure_name else ""
        )
        actions_html = ""
        if a.actions:
            items = "".join(f"<li style='margin-bottom:4px'>{_trunc(act, 160)}</li>" for act in a.actions[:4])
            actions_html = (
                f'<div style="margin-top:8px;font-size:.82em;color:#333">'
                f'<strong>Actions :</strong><ul style="margin:4px 0 0;padding-left:18px">{items}</ul></div>'
            )
        analysis_html = ""
        if a.analysis:
            analysis_html = (
                f'<div style="font-size:.83em;color:#555;font-style:italic;margin-bottom:8px;'
                f'border-left:3px solid {c_crit}40;padding-left:10px">{_trunc(a.analysis, 300)}</div>'
            )
        cards += (
            f'<div style="border:1px solid #e0e0e0;border-radius:8px;margin-bottom:14px;overflow:hidden;page-break-inside:avoid">'
            f'<div style="background:{c_crit}14;border-left:5px solid {c_crit};padding:10px 16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">'
            f'<div style="font-size:1.8em;font-weight:900;color:{c_crit};min-width:28px">{i}</div>'
            f'<div style="flex:1">'
            f'<div style="font-weight:bold;font-size:.95em">{_first_words(a.requirement_id)}{proc_tag}</div>'
            f'<div style="font-size:.82em;color:#666;margin-top:2px">{_trunc(a.thematique, 80)}</div>'
            f'</div>'
            f'<div style="display:flex;gap:6px;flex-wrap:wrap">'
            f'{_badge(a.compliance_level, c_lev, small=True)}'
            f'{_badge(a.criticite, c_crit, small=True)}'
            f'{_badge(a.priorite.split(" - ")[0], c_prio, small=True)}'
            f'</div></div>'
            f'<div style="padding:12px 16px">{analysis_html}'
            f'<div style="font-size:.83em;color:#333;margin-bottom:6px"><strong>Ecart : </strong>{_trunc(a.ecart_description, 260)}</div>'
            f'<div style="font-size:.83em;color:#333"><strong>Recommandation : </strong>{_trunc(a.recommandation, 210)}</div>'
            f'{actions_html}</div></div>'
        )
    return (
        f'<div style="margin-bottom:40px">'
        f'<h2 style="color:{_RED};border-left:5px solid {_RED};padding-left:12px">&#9632; 3. Top 5 Exigences Critiques</h2>'
        f'<p style="font-size:.9em;color:#666;margin-bottom:16px">Les cinq exigences presentant le risque de non-conformite le plus eleve, '
        f'classees par criticite puis niveau de conformite.</p>'
        f"{cards}</div>"
    )


def _plan_actions(extreme: list[RequirementAnalysis]) -> str:
    _prio_bg = {"P1 - Urgente": "#e74c3c", "P2 - Haute": "#e67e22"}
    if not extreme:
        return (
            f"<div style='margin-bottom:40px'><h2 style='color:{_RED};border-left:5px solid {_RED};padding-left:12px'>"
            f"&#9632; 4. Plan d'actions consolide (P1 &amp; P2)</h2>"
            f"<p style='color:#27ae60;padding:16px;background:#eafaf1;border-radius:6px'>Aucune action urgente requise.</p></div>"
        )
    rows = "".join(
        f"<tr style='page-break-inside:avoid;vertical-align:top;{'background:#fafafa;' if i % 2 else ''}'>"
        f"<td style='text-align:center;padding:8px 6px;width:50px'>"
        f"<span style='background:{_prio_bg.get(a.priorite, '#aaa')};color:#fff;padding:3px 7px;"
        f"border-radius:4px;font-weight:bold;font-size:.78em;white-space:nowrap'>{a.priorite.split(' - ')[0]}</span></td>"
        f"<td style='padding:8px 6px;font-size:.82em;white-space:nowrap;width:80px'><strong>{_first_words(a.requirement_id)}</strong>"
        + (f"<br><span style='color:#888;font-size:.78em;font-weight:normal'>{_trunc(a.procedure_name, 30)}</span>" if a.procedure_name else "")
        + f"</td>"
        f"<td style='padding:8px 6px;font-size:.80em;color:#555;width:130px'>{_trunc(a.thematique, 40)}</td>"
        f"<td style='padding:8px 6px;font-size:.82em;line-height:1.45'>{_trunc(a.recommandation, 220)}</td>"
        f"<td style='padding:8px 6px;font-size:.80em;white-space:nowrap;width:100px'>{_trunc(a.echeance_cible, 30)}</td>"
        f"<td style='padding:8px 6px;font-size:.80em;width:150px'>{_trunc(a.responsable_action, 50)}</td></tr>"
        for i, a in enumerate(extreme)
    )
    header = (
        f"<tr style='background:{_RED}'>"
        f"<th style='color:#fff;padding:9px 6px;width:50px'>Prio.</th>"
        f"<th style='color:#fff;padding:9px 6px;width:80px;text-align:left'>Ref.</th>"
        f"<th style='color:#fff;padding:9px 6px;width:130px;text-align:left'>Thematique</th>"
        f"<th style='color:#fff;padding:9px 6px;text-align:left'>Action</th>"
        f"<th style='color:#fff;padding:9px 6px;width:100px;text-align:left'>Echeance</th>"
        f"<th style='color:#fff;padding:9px 6px;width:150px;text-align:left'>Responsable</th></tr>"
    )
    return (
        f"<div style='margin-bottom:40px'><h2 style='color:{_RED};border-left:5px solid {_RED};padding-left:12px'>"
        f"&#9632; 4. Plan d'actions consolide (P1 &amp; P2)</h2>"
        f"<table style='width:100%;border-collapse:collapse;font-size:.88em'>"
        f"<thead>{header}</thead><tbody>{rows}</tbody></table></div>"
    )


# ── public API ────────────────────────────────────────────────────────────────

def generate_html(r: RapportFinal) -> str:
    css = (
        f"*{{box-sizing:border-box}}"
        f"body{{font-family:Arial,Helvetica,sans-serif;max-width:1100px;margin:0 auto;padding:0 24px 40px;color:{_DARK};font-size:14px;line-height:1.5}}"
        f"h1,h2,h3{{page-break-after:avoid;break-after:avoid}}h2{{margin-top:40px;margin-bottom:16px}}h3{{color:{_RED}}}"
        f"table{{width:100%;border-collapse:collapse}}td,th{{word-break:break-word;overflow-wrap:break-word;vertical-align:top}}"
        f"tr{{page-break-inside:avoid;break-inside:avoid}}@media print{{body{{max-width:none;padding:0 16px}}}}"
    )
    extreme = [a for a in r.analyses if a.priorite in ("P1 - Urgente", "P2 - Haute")]
    footer = (
        f"<div style='text-align:center;color:#aaa;font-size:.8em;margin-top:40px;border-top:1px solid #eee;padding-top:16px'>"
        f"BFS Consulting &copy; {datetime.now().year} &mdash; {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>"
    )
    return (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Etude Impact Reglementaire</title><style>{css}</style></head>"
        f"<body>{_cover(r)}{_synthese(r)}{_top5_critiques(r)}{_plan_actions(extreme)}{footer}</body></html>"
    )
