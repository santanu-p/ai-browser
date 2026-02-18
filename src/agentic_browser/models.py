from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CrawlConfig:
    max_pages: int = 50
    max_depth: int = 2
    concurrency: int = 8
    navigation_timeout_ms: int = 10000
    wait_until: str = "domcontentloaded"
    follow_external_links: bool = False
    click_top_candidates: int = 5
    block_assets: bool = True


@dataclass(slots=True)
class PageExtraction:
    url: str
    title: str
    clean_text: str
    metadata: dict[str, Any]
    links: list[str]
    clicked_links: list[str]
    browser_storage: dict[str, Any]


@dataclass(slots=True)
class CrawlResult:
    pages: list[PageExtraction] = field(default_factory=list)

    @property
    def all_text(self) -> str:
        return "\n\n".join(page.clean_text for page in self.pages if page.clean_text)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pages": [
                {
                    "url": p.url,
                    "title": p.title,
                    "clean_text": p.clean_text,
                    "metadata": p.metadata,
                    "links": p.links,
                    "clicked_links": p.clicked_links,
                    "browser_storage": p.browser_storage,
                }
                for p in self.pages
            ]
        }
