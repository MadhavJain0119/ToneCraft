from __future__ import annotations

import argparse
import logging
import sys

from tonecraft.config import settings
from tonecraft.exceptions import ToneCraftError
from tonecraft.ingest import build_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the processed ToneCraft dataset.")
    parser.add_argument("--raw", default=str(settings.raw_dataset_path), help="Path to raw posts JSON.")
    parser.add_argument("--out", default=str(settings.processed_dataset_path), help="Output path.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    try:
        posts = build_dataset(raw_path=args.raw, processed_path=args.out)
    except ToneCraftError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Done. Wrote {len(posts)} posts to {args.out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
