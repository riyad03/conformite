from __future__ import annotations

import html as html_lib
import json

from IPython.display import HTML, display
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

_ROLE_STYLE = {
    "system": ("#1a3a5c", "#e8f4f8", "#2980b9"),
    "human":  ("#1a5c1a", "#f0faf0", "#27ae60"),
    "ai":     ("#5c4a1a", "#fef9e7", "#f39c12"),
}


class IODisplayCallback(BaseCallbackHandler):
    """Notebook callback that renders LLM inputs/outputs as collapsible HTML blocks."""

    def __init__(self, show_inputs: bool = True, show_outputs: bool = True, max_chars: int = 1200):
        self.show_inputs  = show_inputs
        self.show_outputs = show_outputs
        self.max_chars    = max_chars
        self._n           = 0
        self._out_title   = ""

    def _trim(self, text: str) -> str:
        if len(text) > self.max_chars:
            return text[: self.max_chars] + f"\n… [+{len(text) - self.max_chars} chars]"
        return text

    def _role_block(self, role: str, text: str) -> str:
        col, bg, border = _ROLE_STYLE.get(role, ("#333", "#f5f5f5", "#aaa"))
        safe = html_lib.escape(self._trim(text))
        return (
            f'<div style="background:{bg};border-left:3px solid {border};margin:0 0 6px;padding:6px 10px">'
            f'<div style="font-size:.70em;font-weight:bold;color:{col};margin-bottom:3px">{role.upper()}</div>'
            f'<pre style="margin:0;font-size:.78em;white-space:pre-wrap;font-family:monospace;color:#000">{safe}</pre></div>'
        )

    def _details(self, title: str, body_html: str, border: str, bg: str, col: str, open_: bool = False) -> None:
        op = " open" if open_ else ""
        display(HTML(
            f'<details{op} style="margin:4px 0;border:1px solid {border}50;border-radius:6px">'
            f'<summary style="background:{border}12;padding:7px 14px;cursor:pointer;font-weight:bold;color:{col};font-size:.85em">&#9654; {title}</summary>'
            f'<div style="padding:8px;background:{bg}">{body_html}</div></details>'
        ))

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if not self.show_inputs:
            return
        self._n += 1
        model = serialized.get("kwargs", {}).get("model", "LLM").split("/")[-1]
        node  = (kwargs.get("metadata") or {}).get("langgraph_node", "")
        self._out_title = f"#{self._n} ◀ OUTPUT" + (f" · {node}" if node else "")
        blocks = "".join(
            self._role_block(getattr(m, "type", "message").lower(), getattr(m, "content", str(m)))
            for g in messages for m in g
        )
        self._details(
            f"#{self._n} ▶ INPUT" + (f" · {node}" if node else "") + f"  [{model}]",
            blocks, "#2980b9", "#fafafa", "#1a3a5c",
        )

    def on_llm_end(self, response: LLMResult, **kwargs):
        if not self.show_outputs:
            return
        parts = [getattr(g, "text", None) or str(getattr(g, "message", g)) for gens in response.generations for g in gens]
        body  = "\n---\n".join(parts)
        try:
            body = json.dumps(json.loads(body), indent=2, ensure_ascii=False)
        except Exception:
            pass
        self._details(
            self._out_title,
            f'<pre style="margin:0;font-size:.78em;white-space:pre-wrap;font-family:monospace;color:#000">'
            f'{html_lib.escape(self._trim(body))}</pre>',
            "#27ae60", "#f0faf5", "#1a5c38",
        )

    def on_llm_error(self, error, **kwargs):
        self._details(
            f"#{self._n} ✗ ERROR",
            f'<pre style="color:#5c1a1a">{html_lib.escape(str(error))}</pre>',
            "#e74c3c", "#fdf0f0", "#5c1a1a", open_=True,
        )
