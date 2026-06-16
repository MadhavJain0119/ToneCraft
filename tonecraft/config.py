from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from tonecraft.exceptions import ConfigurationError

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger("tonecraft")


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    raw_dataset_path: Path = ROOT_DIR / "data" / "raw_posts.json"
    processed_dataset_path: Path = ROOT_DIR / "data" / "processed_posts.json"

    max_examples: int = 3

    # line-count thresholds for Short / Medium / Long
    short_max_lines: int = 4
    medium_max_lines: int = 10

    supported_languages: tuple[str, ...] = ("English", "Hinglish")
    length_buckets: tuple[str, ...] = ("Short", "Medium", "Long")

    def require_api_key(self) -> str:
        if not self.groq_api_key:
            raise ConfigurationError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
                "Groq API key (get one at https://console.groq.com/keys)."
            )
        return self.groq_api_key


def load_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        model_name=os.getenv("TONECRAFT_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("TONECRAFT_TEMPERATURE", "0.7")),
    )


settings = load_settings()
