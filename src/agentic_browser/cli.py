from __future__ import annotations

import argparse
import asyncio
import json

from .browser import FastAgenticBrowser
from .models import CrawlConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fast agentic browser crawler")
    parser.add_argument("urls", nargs="+", help="Seed URLs")
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--follow-external", action="store_true")
    parser.add_argument("--cache-path", default=".agentic_browser_cache.sqlite3")
    parser.add_argument("--out", default="crawl_output.json")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    config = CrawlConfig(
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        concurrency=args.concurrency,
        follow_external_links=args.follow_external,
    )
    browser = FastAgenticBrowser(config=config, cache_path=args.cache_path)
    result = await browser.crawl(args.urls)
    browser.close()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    print(f"Saved {len(result.pages)} pages to {args.out}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
