from __future__ import annotations

import logging
from functools import lru_cache

from langchain_groq import ChatGroq

from tonecraft.config import Settings, settings
from tonecraft.exceptions import GenerationError

logger = logging.getLogger("tonecraft")


@lru_cache(maxsize=1)
def get_client(cfg: Settings = settings) -> ChatGroq:
    api_key = cfg.require_api_key()
    return ChatGroq(
        groq_api_key=api_key,
        model_name=cfg.model_name,
        temperature=cfg.temperature,
    )


def complete(prompt: str, cfg: Settings = settings) -> str:
    client = get_client(cfg)
    try:
        response = client.invoke(prompt)
    except Exception as exc:
        logger.exception("Language model request failed")
        raise GenerationError(f"Language model request failed: {exc}") from exc

    content = (response.content or "").strip()
    if not content:
        raise GenerationError("Language model returned an empty response.")
    return content


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(complete("Reply with a single word: pong"))
