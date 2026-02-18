from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

IMPORTANT_KEYWORDS = {
    "about",
    "pricing",
    "docs",
    "features",
    "product",
    "blog",
    "contact",
    "api",
    "support",
    "terms",
    "privacy",
    "download",
    "get-started",
}


class _HTMLTextAndLinksParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_ignored_tag = 0
        self.text_parts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg", "canvas", "iframe"}:
            self.in_ignored_tag += 1
        if tag == "a":
            attr_map = dict(attrs)
            href = attr_map.get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg", "canvas", "iframe"} and self.in_ignored_tag:
            self.in_ignored_tag -= 1

    def handle_data(self, data):
        if self.in_ignored_tag:
            return
        cleaned = data.strip()
        if cleaned:
            self.text_parts.append(cleaned)


def extract_clean_text(html: str) -> str:
    parser = _HTMLTextAndLinksParser()
    parser.feed(html)
    text = "\n".join(parser.text_parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_links(base_url: str, html: str, follow_external: bool) -> list[str]:
    parser = _HTMLTextAndLinksParser()
    parser.feed(html)

    base_host = urlparse(base_url).netloc
    found: list[str] = []
    seen = set()

    for href in parser.links:
        href = href.strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if not follow_external and parsed.netloc != base_host:
            continue
        if absolute not in seen:
            seen.add(absolute)
            found.append(absolute)

    return found


def score_link(url: str, text: str = "") -> int:
    normalized = f"{url} {text}".lower()
    score = 0

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in normalized:
            score += 10

    depth_penalty = normalized.count("/")
    score -= min(depth_penalty, 6)

    if "?" in normalized:
        score -= 2

    return score
