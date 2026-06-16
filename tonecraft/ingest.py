from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from tonecraft import llm
from tonecraft.config import Settings, settings
from tonecraft.exceptions import DatasetError

logger = logging.getLogger("tonecraft")

_METADATA_TEMPLATE = """
You are given a social media post. Extract its language and topic tags.
1. Return ONLY valid JSON. No preamble, no markdown fences.
2. The JSON must have exactly two keys: "language" and "tags".
3. "tags" is an array of at most two short, title-cased topic tags.
4. "language" must be either "English" or "Hinglish" (Hinglish = Hindi + English).

Post:
{post}
"""

_UNIFY_TEMPLATE = """
You are given a list of topic tags. Merge near-duplicates into a smaller,
canonical set.
1. Group synonyms, e.g. "Jobseekers" / "Job Hunting" -> "Job Search";
   "Inspiration" / "Drive" -> "Motivation".
2. Every canonical tag must be Title Case.
3. Return ONLY a JSON object mapping each original tag to its canonical tag,
   e.g. {{"Jobseekers": "Job Search", "Job Hunting": "Job Search"}}.

Tags:
{tags}
"""


def _count_content_lines(text: str) -> int:
    return sum(1 for line in text.split("\n") if line.strip())


def _parse_json(raw: str) -> dict:
    try:
        return JsonOutputParser().parse(raw)
    except OutputParserException as exc:
        raise DatasetError(f"Model returned unparseable JSON: {exc}") from exc


def extract_metadata(post_text: str, cfg: Settings = settings) -> dict:
    prompt = PromptTemplate.from_template(_METADATA_TEMPLATE).format(post=post_text)
    meta = _parse_json(llm.complete(prompt, cfg))
    meta["line_count"] = _count_content_lines(post_text)
    meta.setdefault("tags", [])
    return meta


def unify_tags(posts: list[dict], cfg: Settings = settings) -> dict[str, str]:
    all_tags = sorted({tag for post in posts for tag in post.get("tags", [])})
    if not all_tags:
        return {}
    prompt = PromptTemplate.from_template(_UNIFY_TEMPLATE).format(tags=", ".join(all_tags))
    mapping = _parse_json(llm.complete(prompt, cfg))
    return {tag: mapping.get(tag, tag) for tag in all_tags}


def build_dataset(
    raw_path: Path | None = None,
    processed_path: Path | None = None,
    cfg: Settings = settings,
) -> list[dict]:
    raw_path = Path(raw_path or cfg.raw_dataset_path)
    processed_path = Path(processed_path or cfg.processed_dataset_path)

    if not raw_path.exists():
        raise DatasetError(f"Raw dataset not found at '{raw_path}'.")

    with raw_path.open(encoding="utf-8") as handle:
        raw_posts = json.load(handle)

    logger.info("Enriching %d raw posts...", len(raw_posts))
    enriched: list[dict] = []
    for index, post in enumerate(raw_posts, start=1):
        metadata = extract_metadata(post["text"], cfg)
        enriched.append({**post, **metadata})
        logger.info("  [%d/%d] tags=%s", index, len(raw_posts), metadata.get("tags"))

    tag_map = unify_tags(enriched, cfg)
    for post in enriched:
        post["tags"] = sorted({tag_map.get(tag, tag) for tag in post.get("tags", [])})

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    with processed_path.open("w", encoding="utf-8") as handle:
        json.dump(enriched, handle, ensure_ascii=False, indent=2)
    logger.info("Wrote %d processed posts to %s", len(enriched), processed_path)
    return enriched
