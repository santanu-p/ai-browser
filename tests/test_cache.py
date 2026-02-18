from pathlib import Path

from agentic_browser.cache import Cache


def test_flush_makes_data_durable(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.db"
    cache = Cache(db_path, flush_every=1000)
    cache.put("a", b"1")

    # Not guaranteed durable until explicit flush.
    cache.flush()
    cache.close()

    reopened = Cache(db_path)
    assert reopened.get("a") == b"1"
    reopened.close()


def test_close_flushes_pending_data(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.db"
    cache = Cache(db_path, flush_every=1000)
    cache.put("k", b"v")
    cache.close()

    reopened = Cache(db_path)
    assert reopened.get("k") == b"v"
    reopened.close()
