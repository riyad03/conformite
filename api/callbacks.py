"""StreamingCallback — emits LangGraph node events into an asyncio.Queue for SSE."""
from __future__ import annotations

import asyncio
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


def _safe(obj, depth: int = 0):
    """Recursively convert any object to a JSON-safe structure, truncating large values."""
    if depth > 3:
        return "…"
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return obj[:600] + ("…" if len(obj) > 600 else "")
    if isinstance(obj, dict):
        return {k: _safe(v, depth + 1) for k, v in list(obj.items())[:12]}
    if isinstance(obj, (list, tuple)):
        return [_safe(v, depth + 1) for v in list(obj)[:8]]
    if hasattr(obj, "model_dump"):
        return _safe(obj.model_dump(), depth + 1)
    if hasattr(obj, "content"):
        return {"role": getattr(obj, "type", "?"), "content": _safe(str(getattr(obj, "content", "")), depth + 1)}
    return str(obj)[:400]


class StreamingCallback(BaseCallbackHandler):
    """Forwards LangGraph node and LLM events to an asyncio.Queue for SSE streaming."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        self._q    = queue
        self._loop = loop

    def _emit(self, event: dict) -> None:
        try:
            self._loop.call_soon_threadsafe(self._q.put_nowait, event)
        except Exception:
            pass

    def _node(self, kwargs: dict) -> str | None:
        return (kwargs.get("metadata") or {}).get("langgraph_node")

    # ── node lifecycle ────────────────────────────────────────────────────────

    def on_chain_start(self, serialized, inputs, **kwargs):
        node = self._node(kwargs)
        if node:
            self._emit({"type": "node_start", "node": node, "input": _safe(inputs)})

    def on_chain_end(self, outputs, **kwargs):
        node = self._node(kwargs)
        if node:
            self._emit({"type": "node_end", "node": node, "output": _safe(outputs)})

    def on_chain_error(self, error, **kwargs):
        node = self._node(kwargs) or "unknown"
        self._emit({"type": "node_error", "node": node, "error": str(error)})

    # ── LLM calls ─────────────────────────────────────────────────────────────

    def on_chat_model_start(self, serialized, messages, **kwargs):
        node = self._node(kwargs) or "unknown"
        msgs = [
            {"role": getattr(m, "type", "message"), "content": _safe(str(getattr(m, "content", "")))}
            for group in messages for m in group
        ]
        self._emit({"type": "llm_start", "node": node, "messages": msgs})

    def on_llm_end(self, response: LLMResult, **kwargs):
        node = self._node(kwargs) or "unknown"
        parts = [
            getattr(g, "text", None) or str(getattr(g, "message", g))
            for gens in response.generations for g in gens
        ]
        self._emit({"type": "llm_end", "node": node, "response": _safe("\n---\n".join(parts))})
