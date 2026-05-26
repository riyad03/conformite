"""Expose default agent system prompts so the UI can display and edit them."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/prompts")
def get_agent_prompts() -> dict[str, str]:
    from module_folder.agents.prompts import get_default_prompts
    return get_default_prompts()
