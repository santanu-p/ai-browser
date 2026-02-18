"""Browser helpers for extracting storage state from a page."""

from __future__ import annotations

from typing import Any


class AgenticBrowser:
    """Minimal browser helper utilities."""

    async def _extract_browser_storage(self, page: Any) -> dict[str, Any]:
        """Extract browser storage in a fault-tolerant way.

        Returns storage values plus a ``storageErrors`` object with backend-specific
        failures. Individual backend failures do not fail extraction.
        """

        return await page.evaluate(
            """
            () => {
              const result = {
                localStorage: {},
                sessionStorage: {},
                indexedDB: [],
                storageErrors: {},
              };

              try {
                const localEntries = {};
                for (let i = 0; i < localStorage.length; i++) {
                  const key = localStorage.key(i);
                  localEntries[key] = localStorage.getItem(key);
                }
                result.localStorage = localEntries;
              } catch (error) {
                result.storageErrors.localStorage = String(error);
              }

              try {
                const sessionEntries = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                  const key = sessionStorage.key(i);
                  sessionEntries[key] = sessionStorage.getItem(key);
                }
                result.sessionStorage = sessionEntries;
              } catch (error) {
                result.storageErrors.sessionStorage = String(error);
              }

              try {
                if (indexedDB && indexedDB.databases) {
                  result.indexedDB = indexedDB.databases();
                } else {
                  result.indexedDB = [];
                }
              } catch (error) {
                result.storageErrors.indexedDB = String(error);
                result.indexedDB = [];
              }

              return result;
            }
            """
        )
