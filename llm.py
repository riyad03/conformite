from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

_llm: ChatAnthropic | None = None


def get_llm() -> ChatAnthropic:
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=os.getenv("MODEL_NAME", "claude-sonnet-4-6"),
            api_key=os.getenv("TEMP_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("TEMP_BASE_URL"),
            max_tokens=16384,
        )
    return _llm
