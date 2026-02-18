from agentic_browser.cache import CrawlCache


def test_cache_put_get(tmp_path):
    db = tmp_path / "cache.sqlite3"
    cache = CrawlCache(str(db))
    payload = {
        "url": "https://example.com",
        "title": "Example",
        "clean_text": "Hello",
        "metadata": {"a": 1},
        "links": ["https://example.com/docs"],
        "clicked_links": [],
        "browser_storage": {"localStorage": {}},
    }
    cache.put(payload)
    got = cache.get("https://example.com")
    cache.close()

    assert got is not None
    assert got["title"] == "Example"
    assert got["metadata"]["a"] == 1
