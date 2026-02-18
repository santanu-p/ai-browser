from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Tuple


class Cache:
    """SQLite-backed key/value cache with buffered writes."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        flush_every: int = 500,
        cache_size: int = -20000,
    ) -> None:
        self._path = str(db_path)
        self._conn = sqlite3.connect(self._path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(f"PRAGMA cache_size={int(cache_size)}")

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL
            )
            """
        )
        self._conn.commit()

        self._flush_every = max(1, flush_every)
        self._pending_writes = 0

    def put(self, key: str, value: bytes) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO cache(key, value) VALUES(?, ?)",
            (key, value),
        )
        self._pending_writes += 1
        if self._pending_writes >= self._flush_every:
            self.flush()

    def put_many(self, rows: Iterable[Tuple[str, bytes]]) -> None:
        buffered_rows = list(rows)
        if not buffered_rows:
            return

        self._conn.executemany(
            "INSERT OR REPLACE INTO cache(key, value) VALUES(?, ?)",
            buffered_rows,
        )
        self._pending_writes += len(buffered_rows)
        if self._pending_writes >= self._flush_every:
            self.flush()

    def get(self, key: str) -> Optional[bytes]:
        row = self._conn.execute(
            "SELECT value FROM cache WHERE key = ?",
            (key,),
        ).fetchone()
        return row[0] if row else None

    def flush(self) -> None:
        self._conn.commit()
        self._pending_writes = 0

    def close(self) -> None:
        self.flush()
        self._conn.close()
