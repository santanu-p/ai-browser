from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class CrawlCache:
    def __init__(self, db_path: str = ".agentic_browser_cache.sqlite3") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                clean_text TEXT NOT NULL,
                metadata TEXT NOT NULL,
                links TEXT NOT NULL,
                clicked_links TEXT NOT NULL,
                browser_storage TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def get(self, url: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT title, clean_text, metadata, links, clicked_links, browser_storage
            FROM pages
            WHERE url = ?
            """,
            (url,),
        ).fetchone()
        if not row:
            return None

        return {
            "url": url,
            "title": row[0],
            "clean_text": row[1],
            "metadata": json.loads(row[2]),
            "links": json.loads(row[3]),
            "clicked_links": json.loads(row[4]),
            "browser_storage": json.loads(row[5]),
        }

    def put(self, payload: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO pages (url, title, clean_text, metadata, links, clicked_links, browser_storage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                clean_text=excluded.clean_text,
                metadata=excluded.metadata,
                links=excluded.links,
                clicked_links=excluded.clicked_links,
                browser_storage=excluded.browser_storage,
                fetched_at=CURRENT_TIMESTAMP
            """,
            (
                payload["url"],
                payload["title"],
                payload["clean_text"],
                json.dumps(payload["metadata"]),
                json.dumps(payload["links"]),
                json.dumps(payload["clicked_links"]),
                json.dumps(payload["browser_storage"]),
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
