from __future__ import annotations

import argparse
import asyncio
import json

from .browser import FastAgenticBrowser
from .cache import CrawlCache
from .models import CrawlConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fast agentic browser crawler")
    parser.add_argument("urls", nargs="*", help="Seed URLs")
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--follow-external", action="store_true")
    parser.add_argument("--cache-path", default=".agentic_browser_cache.sqlite3")
    parser.add_argument("--out", default="crawl_output.json")
    parser.add_argument("--query", help="Search the crawler SQLite cache and print matching pages")
    parser.add_argument("--query-limit", type=int, default=20)
    parser.add_argument(
        "--allow-assets",
        action="store_true",
        help="Do not block images/fonts/media/stylesheets during crawl",
    )
    return parser.parse_args()


async def run() -> None:
    args = parse_args()

    if args.query:
        cache = CrawlCache(args.cache_path)
        rows = cache.query(args.query, limit=args.query_limit)
        cache.close()
        print(json.dumps({"matches": rows}, indent=2, ensure_ascii=False))
        return

    if not args.urls:
        raise SystemExit("Provide at least one URL or pass --query")

    config = CrawlConfig(
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        concurrency=args.concurrency,
        follow_external_links=args.follow_external,
        block_assets=not args.allow_assets,
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
