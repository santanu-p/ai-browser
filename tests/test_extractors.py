from agentic_browser.extractors import extract_clean_text, extract_links, score_link


def test_extract_clean_text_removes_scripts():
    html = """
    <html><body><main><h1>Hello</h1><script>alert(1)</script><p>World</p></main></body></html>
    """
    text = extract_clean_text(html)
    assert "Hello" in text
    assert "World" in text
    assert "alert" not in text


def test_extract_links_same_host_only_by_default():
    html = '<a href="/docs">Docs</a><a href="https://external.com">x</a>'
    links = extract_links("https://example.com", html, follow_external=False)
    assert links == ["https://example.com/docs"]


def test_score_link_prefers_relevant_paths():
    assert score_link("https://example.com/docs") > score_link("https://example.com/x")
