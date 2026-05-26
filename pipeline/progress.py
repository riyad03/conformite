"""Thread-safe progress emitter for SSE streaming."""
from __future__ import annotations
import threading

_lock     = threading.Lock()
_callback = None


def set_callback(fn) -> None:
    global _callback
    with _lock:
        _callback = fn


def clear_callback() -> None:
    global _callback
    with _lock:
        _callback = None


def emit(node: str, current: int, total: int, label: str = "") -> None:
    with _lock:
        fn = _callback
    if fn:
        try:
            fn({"type": "progress", "node": node, "current": current, "total": total, "label": label})
        except Exception:
            pass
