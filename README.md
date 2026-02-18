# Agentic Browser (Fast)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santanu-p/ai-browser/blob/main/notebooks/agentic_browser_colab.ipynb)

A highly optimized **AI-agentic browser crawler** designed to:

- Crawl websites concurrently at high speed.
- Prioritize and click the most relevant links (docs, pricing, product, API, support, etc.).
- Extract clean text and metadata from each page.
- Fetch browser-side data (localStorage, sessionStorage, indexedDB names, cookies).
- Cache crawl results in a SQLite "browser database" for fast repeated queries.

## Why this is fast

- **Async concurrency** with configurable worker count.
- **DOM-content-loaded strategy** (not full network-idle) for quick extraction.
- **Heuristic link scoring** to click high-signal pages first.
- **SQLite cache** to skip repeat fetches and query already-crawled content instantly.
- **Network resource blocking** (images/fonts/media/CSS) for significantly faster page turns.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
playwright install chromium
```

## Run in Google Colab

Click the **Open in Colab** button above, then run all cells in the notebook.

The notebook will:

1. Clone this repo into Colab.
2. Install dependencies and Playwright Chromium.
3. Run a sample crawl and save `out.json`.
4. Run a sample cache query.

> If this repository lives under a different GitHub account or branch, update the repo URL in the first notebook cell (and optionally this badge link) to your fork/path.

## Usage

```bash
agentic-browser https://example.com --max-pages 40 --max-depth 2 --concurrency 10 --out out.json
```

Options:

- `--follow-external`: include external domains.
- `--cache-path`: path to SQLite cache database.
- `--allow-assets`: disable speed optimization and allow heavy assets.
- `--query "term"`: search the local crawl database quickly without re-crawling.

## Output

`out.json` contains per-page:

- `url`, `title`
- `clean_text`
- `metadata` (depth, host, text length, link count)
- `links`
- `clicked_links`
- `browser_storage` (`localStorage`, `sessionStorage`, indexedDB DB names, cookies)

## Example (Python API)

```python
import asyncio
from agentic_browser.models import CrawlConfig
from agentic_browser.browser import FastAgenticBrowser

async def main():
    crawler = FastAgenticBrowser(
        CrawlConfig(max_pages=50, max_depth=2, concurrency=8)
    )
    result = await crawler.crawl(["https://example.com"])
    crawler.close()
    print(result.all_text[:500])

asyncio.run(main())
```


## Query cached browser database

```bash
agentic-browser --cache-path .agentic_browser_cache.sqlite3 --query "pricing" --query-limit 10
```

This returns matched pages from SQLite (`url`, `title`, `clean_text`, links, metadata, browser storage).
