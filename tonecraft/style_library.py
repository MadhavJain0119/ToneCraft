from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from tonecraft.config import Settings, settings
from tonecraft.exceptions import DatasetError

logger = logging.getLogger("tonecraft")


class StyleLibrary:
    def __init__(self, cfg: Settings = settings, dataset_path: Path | None = None):
        self._cfg = cfg
        self._path = Path(dataset_path or cfg.processed_dataset_path)
        self._frame = self._load()

    def _load(self) -> pd.DataFrame:
        if not self._path.exists():
            raise DatasetError(
                f"Processed dataset not found at '{self._path}'. "
                "Run `python -m scripts.build_dataset` first."
            )
        try:
            with self._path.open(encoding="utf-8") as handle:
                posts = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise DatasetError(f"Could not read dataset '{self._path}': {exc}") from exc

        if not posts:
            raise DatasetError(f"Dataset '{self._path}' is empty.")

        frame = pd.json_normalize(posts)
        required = {"text", "language", "tags", "line_count"}
        missing = required - set(frame.columns)
        if missing:
            raise DatasetError(f"Dataset is missing required fields: {sorted(missing)}")

        frame["length"] = frame["line_count"].apply(self._bucket_length)
        logger.info("Loaded %d posts from %s", len(frame), self._path)
        return frame

    def _bucket_length(self, line_count: int) -> str:
        if line_count <= self._cfg.short_max_lines:
            return "Short"
        if line_count <= self._cfg.medium_max_lines:
            return "Medium"
        return "Long"

    def topics(self) -> list[str]:
        tags = {tag for tag_list in self._frame["tags"] for tag in tag_list}
        return sorted(tags)

    def examples_for(self, *, length: str, language: str, topic: str) -> list[dict]:
        mask = (
            self._frame["tags"].apply(lambda tags: topic in tags)
            & (self._frame["language"] == language)
            & (self._frame["length"] == length)
        )
        matches = self._frame[mask]
        if "engagement" in matches.columns:
            matches = matches.sort_values("engagement", ascending=False)
        return matches.to_dict(orient="records")

    @property
    def size(self) -> int:
        return len(self._frame)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    library = StyleLibrary()
    print("Topics:", library.topics())
    print("Sample:", library.examples_for(length="Medium", language="Hinglish", topic="Job Search"))
