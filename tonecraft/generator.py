from __future__ import annotations

import logging

from tonecraft import llm
from tonecraft.config import Settings, settings
from tonecraft.exceptions import GenerationError
from tonecraft.style_library import StyleLibrary

logger = logging.getLogger("tonecraft")

_LENGTH_HINTS = {
    "Short": "1 to 4 lines",
    "Medium": "5 to 10 lines",
    "Long": "11 to 15 lines",
}


class PostGenerator:
    def __init__(self, library: StyleLibrary | None = None, cfg: Settings = settings):
        self._cfg = cfg
        self._library = library or StyleLibrary(cfg)

    @property
    def library(self) -> StyleLibrary:
        return self._library

    def generate(self, *, topic: str, length: str, language: str) -> str:
        self._validate(length=length, language=language)
        prompt = self.build_prompt(topic=topic, length=length, language=language)
        return llm.complete(prompt, self._cfg)

    def _validate(self, *, length: str, language: str) -> None:
        if length not in self._cfg.length_buckets:
            raise GenerationError(
                f"Unknown length '{length}'. Expected one of {self._cfg.length_buckets}."
            )
        if language not in self._cfg.supported_languages:
            raise GenerationError(
                f"Unsupported language '{language}'. Expected one of "
                f"{self._cfg.supported_languages}."
            )

    def build_prompt(self, *, topic: str, length: str, language: str) -> str:
        length_hint = _LENGTH_HINTS.get(length, "a few lines")

        lines = [
            "Generate a LinkedIn post using the information below. No preamble.",
            "",
            f"1) Topic: {topic}",
            f"2) Length: {length_hint}",
            f"3) Language: {language}",
            "   If the language is Hinglish it means a natural mix of Hindi and "
            "English, but always written in the English (Latin) script.",
        ]

        examples = self._library.examples_for(length=length, language=language, topic=topic)
        examples = examples[: self._cfg.max_examples]

        if examples:
            lines.append("4) Match the author's writing style as shown in these examples:")
            for i, post in enumerate(examples, start=1):
                lines.append(f"\nExample {i}:\n{post['text']}")
        else:
            logger.info(
                "No style examples for topic=%s length=%s language=%s; generating without few-shot.",
                topic, length, language,
            )

        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = PostGenerator()
    print(generator.generate(topic="Career Growth", length="Medium", language="English"))
