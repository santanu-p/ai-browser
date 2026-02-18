from __future__ import annotations

import asyncio
from collections import deque
from typing import Iterable
from urllib.parse import urlparse

from playwright.async_api import Browser, Page, async_playwright

from .cache import CrawlCache
from .extractors import extract_clean_text, extract_links, score_link
from .models import CrawlConfig, CrawlResult, PageExtraction


class FastAgenticBrowser:
    """High-performance async crawler with lightweight agentic click strategy."""

    def __init__(self, config: CrawlConfig | None = None, cache_path: str | None = None):
        self.config = config or CrawlConfig()
        self.cache = CrawlCache(cache_path or ".agentic_browser_cache.sqlite3")

    async def crawl(self, seeds: Iterable[str]) -> CrawlResult:
        queue = deque((url, 0) for url in seeds)
        visited: set[str] = set()
        result = CrawlResult()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            sem = asyncio.Semaphore(self.config.concurrency)

            async def worker(url: str, depth: int):
                async with sem:
                    if url in visited:
                        return []
                    visited.add(url)
                    page_data, discovered = await self._process_url(browser, url, depth)
                    if page_data:
                        result.pages.append(page_data)
                    return discovered

            while queue and len(result.pages) < self.config.max_pages:
                batch = []
                while queue and len(batch) < self.config.concurrency:
                    url, depth = queue.popleft()
                    if depth > self.config.max_depth:
                        continue
                    batch.append(asyncio.create_task(worker(url, depth)))

                if not batch:
                    break

                for future in asyncio.as_completed(batch):
                    discovered = await future
                    for next_url, next_depth in discovered:
                        if next_url not in visited and next_depth <= self.config.max_depth:
                            queue.append((next_url, next_depth))

            await browser.close()

        return result

    async def _process_url(self, browser: Browser, url: str, depth: int):
        cached = self.cache.get(url)
        if cached:
            return PageExtraction(**cached), []

        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(
                url,
                timeout=self.config.navigation_timeout_ms,
                wait_until=self.config.wait_until,
            )
            html = await page.content()
            title = await page.title()

            text = extract_clean_text(html)
            links = extract_links(url, html, self.config.follow_external_links)
            clicked_links = await self._click_promising_links(page, links)
            browser_storage = await self._extract_browser_storage(page)
            metadata = {
                "depth": depth,
                "final_url": page.url,
                "host": urlparse(page.url).netloc,
                "text_length": len(text),
                "link_count": len(links),
            }

            extracted = PageExtraction(
                url=url,
                title=title,
                clean_text=text,
                metadata=metadata,
                links=links,
                clicked_links=clicked_links,
                browser_storage=browser_storage,
            )
            self.cache.put(extracted.__dict__)

            discovered = [(link, depth + 1) for link in links]
            discovered.extend((link, depth + 1) for link in clicked_links if link not in links)
            return extracted, discovered
        except Exception as exc:
            failure = PageExtraction(
                url=url,
                title="",
                clean_text="",
                metadata={"error": str(exc), "depth": depth},
                links=[],
                clicked_links=[],
                browser_storage={},
            )
            return failure, []
        finally:
            await context.close()

    async def _click_promising_links(self, page: Page, links: list[str]) -> list[str]:
        candidates = sorted(
            links,
            key=lambda u: score_link(u),
            reverse=True,
        )[: self.config.click_top_candidates]

        clicked: list[str] = []
        for target in candidates:
            try:
                await page.goto(
                    target,
                    timeout=self.config.navigation_timeout_ms,
                    wait_until=self.config.wait_until,
                )
                clicked.append(page.url)
            except Exception:
                continue

        return clicked

    async def _extract_browser_storage(self, page: Page) -> dict:
        return await page.evaluate(
            """
            async () => {
              const local = {};
              const session = {};

              for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                local[key] = localStorage.getItem(key);
              }

              for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                session[key] = sessionStorage.getItem(key);
              }

              const indexedDbNames = (await indexedDB.databases()).map(db => db.name).filter(Boolean);

              return {
                localStorage: local,
                sessionStorage: session,
                indexedDB: indexedDbNames,
                cookies: document.cookie
              };
            }
            """
        )

    def close(self) -> None:
        self.cache.close()
