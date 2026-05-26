from __future__ import annotations

from datetime import datetime

_RED  = "#c0392b"
_DARK = "#1a1a1a"


def _fw(text: str, n: int = 2) -> str:
    words = (text or "").split()
    return text if len(words) <= n else " ".join(words[:n]) + "…"


def generate_validation_html(
    validation_results: dict,
    procedure_name: str,
    selected_processes: list[str],
) -> str:
    req_order   = list(validation_results.keys())
    total       = len(req_order)
    nb_relevant = sum(1 for v in validation_results.values() if v["is_relevant"])
    nb_excluded = total - nb_relevant
    pct         = int(nb_relevant / max(total, 1) * 100)

    gauge = (
        f'<div style="background:#ecf0f1;border-radius:6px;height:22px;overflow:hidden;margin:8px 0">'
        f'<div style="width:{pct}%;background:#2980b9;height:100%;display:flex;align-items:center;'
        f'justify-content:center;color:#fff;font-weight:bold;font-size:.85em">{pct}%</div></div>'
    )
    indicators = (
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin:16px 0">'
        f'<div style="flex:1;min-width:120px;background:#eaf4fb;border-radius:8px;padding:12px;text-align:center">'
        f'<div style="font-size:2em;font-weight:900;color:#2980b9">{total}</div>'
        f'<div style="font-size:.8em;color:#555">Total exigences</div></div>'
        f'<div style="flex:1;min-width:120px;background:#eafaf1;border-radius:8px;padding:12px;text-align:center">'
        f'<div style="font-size:2em;font-weight:900;color:#27ae60">{nb_relevant}</div>'
        f'<div style="font-size:.8em;color:#555">Concernées</div></div>'
        f'<div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:8px;padding:12px;text-align:center">'
        f'<div style="font-size:2em;font-weight:900;color:#7f8c8d">{nb_excluded}</div>'
        f'<div style="font-size:.8em;color:#555">Non concernées</div></div>'
        f'</div>'
    )
    rows = "".join(
        f"<tr style='vertical-align:top;{'background:#fafafa;' if i % 2 else ''}'>"
        f"<td style='padding:8px 10px;font-weight:bold;white-space:nowrap;font-size:.85em;width:100px'>{_fw(rid)}</td>"
        f"<td style='padding:8px 10px;font-size:.82em;color:#444;width:40%'>"
        + (v["req_text"][:180] + "…" if len(v["req_text"]) > 180 else v["req_text"])
        + "</td>"
        f"<td style='padding:8px 10px;text-align:center;width:110px'>"
        + (
            "<span style='background:#27ae60;color:#fff;padding:3px 10px;border-radius:4px;font-size:.8em;font-weight:bold'>CONCERNÉE</span>"
            if v["is_relevant"] else
            "<span style='background:#95a5a6;color:#fff;padding:3px 10px;border-radius:4px;font-size:.8em'>Exclue</span>"
        )
        + "</td>"
        f"<td style='padding:8px 10px;font-size:.82em;color:#555;font-style:italic'>"
        + (v["reason"][:200] + "…" if len(v.get("reason", "")) > 200 else v.get("reason", "—"))
        + "</td></tr>"
        for i, (rid, v) in enumerate(validation_results.items())
    )
    css = (
        "*{box-sizing:border-box}"
        "body{font-family:Arial,Helvetica,sans-serif;max-width:1100px;margin:0 auto;padding:0 24px 40px;color:#1a1a1a;font-size:14px;line-height:1.5}"
        "h1,h2{page-break-after:avoid} h2{margin-top:32px;margin-bottom:12px}"
        "table{width:100%;border-collapse:collapse} td,th{word-break:break-word;overflow-wrap:break-word}"
        "tr{page-break-inside:avoid}"
    )
    return (
        '<!DOCTYPE html><html lang="fr">'
        '<head><meta charset="UTF-8"><title>Rapport Validation</title>'
        f'<style>{css}</style></head><body>'
        f'<div style="background:{_RED};padding:20px 32px">'
        f'<div style="color:#fff;font-weight:900;letter-spacing:2px">BFS CONSULTING</div>'
        f'<div style="color:#ffcccc;font-size:.8em">Governance &bull; Risk &bull; Compliance</div></div>'
        f'<div style="padding:32px 0 16px">'
        f'<h1 style="margin:0 0 4px;color:{_DARK}">Rapport de Validation des Exigences</h1>'
        f'<div style="color:#666;font-size:.9em">Procédure : <strong>{procedure_name}</strong>'
        f' &nbsp;|&nbsp; Processus : {", ".join(selected_processes)}'
        f' &nbsp;|&nbsp; {datetime.now().strftime("%d/%m/%Y")}</div></div>'
        f'{indicators}{gauge}'
        f'<h2 style="color:{_RED};border-left:5px solid {_RED};padding-left:12px">Résultats par exigence</h2>'
        f'<table><thead><tr style="background:{_DARK}">'
        f'<th style="color:#fff;padding:9px 10px;text-align:left">Ref.</th>'
        f'<th style="color:#fff;padding:9px 10px;text-align:left">Exigence</th>'
        f'<th style="color:#fff;padding:9px 10px">Statut</th>'
        f'<th style="color:#fff;padding:9px 10px;text-align:left">Justification</th>'
        f'</tr></thead><tbody>{rows}</tbody></table>'
        f'<div style="text-align:center;color:#aaa;font-size:.8em;margin-top:32px;border-top:1px solid #eee;padding-top:12px">'
        f'BFS Consulting &copy; {datetime.now().year} &mdash; {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>'
        '</body></html>'
    )
