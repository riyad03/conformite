from __future__ import annotations


def get_default_prompts() -> dict[str, str]:
    from module_folder.agents.validateur import DEFAULT_SYSTEM as validateur
    from module_folder.agents.summarizer import DEFAULT_SYSTEM as summarizer
    from module_folder.agents.analyste   import DEFAULT_SYSTEM as analyste
    from module_folder.agents.evaluateur import DEFAULT_SYSTEM as evaluateur
    return {
        "validateur": validateur,
        "summarizer": summarizer,
        "analyste":   analyste,
        "evaluateur": evaluateur,
    }
