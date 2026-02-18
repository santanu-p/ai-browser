import pytest

playwright = pytest.importorskip("playwright.async_api")

from agentic_browser.browser import AgenticBrowser


@pytest.mark.asyncio
async def test_extract_browser_storage_handles_blocked_session_storage():
    browser_helper = AgenticBrowser()

    async with playwright.async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        await page.add_init_script(
            """
            Object.defineProperty(window, 'sessionStorage', {
              configurable: true,
              get() {
                throw new Error('session storage blocked');
              },
            });
            """
        )

        await page.goto("data:text/html,<html><body>ok</body></html>")
        await page.evaluate("""() => localStorage.setItem('foo', 'bar')""")

        storage = await browser_helper._extract_browser_storage(page)

        assert storage["localStorage"]["foo"] == "bar"
        assert storage["sessionStorage"] == {}
        assert storage["indexedDB"] == [] or isinstance(storage["indexedDB"], list)
        assert "sessionStorage" in storage["storageErrors"]
        assert "session storage blocked" in storage["storageErrors"]["sessionStorage"]

        await context.close()
        await browser.close()
