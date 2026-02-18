from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page


@dataclass(slots=True)
class LinkCandidate:
    """A visible clickable candidate extracted from the current DOM."""

    selector: str
    text: str
    href: str | None
    role: str | None
    tag: str


class AgenticBrowser:
    """Small browser helper that prioritizes promising click targets."""

    def __init__(self) -> None:
        self.clicked_links: list[dict[str, Any]] = []
        self.crawl_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def _extract_click_candidates(self, page: Page) -> list[LinkCandidate]:
        """Query visible clickable elements and return lightweight metadata."""
        handles = await page.query_selector_all("a, button, [role=button]")
        candidates: list[LinkCandidate] = []

        for handle in handles:
            is_visible = await handle.is_visible()
            if not is_visible:
                continue

            text = ((await handle.inner_text()) or "").strip()
            href = await handle.get_attribute("href")
            tag = (await handle.evaluate("el => el.tagName.toLowerCase()"))
            role = await handle.get_attribute("role")
            selector = await self._selector_hint(handle)

            if not selector:
                continue

            candidates.append(
                LinkCandidate(
                    selector=selector,
                    text=text,
                    href=href,
                    role=role,
                    tag=tag,
                )
            )

        return candidates

    async def _selector_hint(self, handle: Any) -> str | None:
        return await handle.evaluate(
            """
            el => {
              if (el.id) return `#${el.id}`;
              if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
              const cls = [...el.classList].slice(0, 2).join('.');
              if (cls) return `${el.tagName.toLowerCase()}.${cls}`;
              return el.tagName.toLowerCase();
            }
            """
        )

    def score_link(
        self,
        url: str | None,
        text: str,
        metadata: dict[str, Any],
        query_terms: list[str],
    ) -> float:
        """Score using URL + visible text + simple metadata signals."""
        haystacks = [text.lower()]
        if url:
            haystacks.append(url.lower())

        score = 0.0
        for term in query_terms:
            token = term.lower().strip()
            if not token:
                continue
            for haystack in haystacks:
                if token in haystack:
                    score += 1.0

        if metadata.get("tag") == "a" and url:
            score += 0.2
        if metadata.get("role") == "button":
            score += 0.1

        return score

    def _same_origin(self, current_url: str, target_url: str) -> bool:
        current = urlparse(current_url)
        target = urlparse(target_url)
        return (current.scheme, current.netloc) == (target.scheme, target.netloc)

    def _safe_click_context(self, current_url: str) -> bool:
        parsed = urlparse(current_url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    async def _enqueue_crawl_task(self, target_url: str, provenance: dict[str, Any]) -> None:
        await self.crawl_queue.put(
            {
                "url": target_url,
                "provenance": provenance,
            }
        )

    async def _click_promising_links(
        self,
        page: Page,
        query_terms: list[str],
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Rank candidates, queue URL crawls, and click only when navigation URL is unavailable."""
        current_url = page.url
        candidates = await self._extract_click_candidates(page)

        scored: list[tuple[float, LinkCandidate, str | None]] = []
        for candidate in candidates:
            resolved_url = urljoin(current_url, candidate.href) if candidate.href else None
            score = self.score_link(
                resolved_url,
                candidate.text,
                {
                    "selector": candidate.selector,
                    "tag": candidate.tag,
                    "role": candidate.role,
                },
                query_terms,
            )
            if score > 0:
                scored.append((score, candidate, resolved_url))

        scored.sort(key=lambda item: item[0], reverse=True)

        actions: list[dict[str, Any]] = []
        for score, candidate, resolved_url in scored[:top_n]:
            provenance = {
                "selector": candidate.selector,
                "text": candidate.text,
                "url": resolved_url,
                "score": score,
            }

            if resolved_url:
                await self._enqueue_crawl_task(resolved_url, provenance)
                event = {**provenance, "action": "queued_url_crawl"}
                self.clicked_links.append(event)
                actions.append(event)
                continue

            if not self._safe_click_context(current_url):
                continue

            await page.click(candidate.selector)
            event = {**provenance, "action": "clicked_selector"}
            self.clicked_links.append(event)
            actions.append(event)

        return actions
