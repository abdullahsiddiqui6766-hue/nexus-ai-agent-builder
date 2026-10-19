from __future__ import annotations

import logging

from ddgs import DDGS

from tools.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoSearchProvider(SearchProvider):
    """Web search provider powered by the DDGS package."""

    def __init__(self, timeout: float = 15.0) -> None:
        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero.")

        self.timeout = timeout

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """Return web results with their original titles, URLs, and snippets."""

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if max_results < 1:
            raise ValueError("max_results must be positive.")

        try:
            with DDGS(timeout=self.timeout) as search_client:
                raw_results = search_client.text(
                    query.strip(),
                    max_results=min(max_results, 8),
                )

                results: list[SearchResult] = []
                seen_urls: set[str] = set()

                for item in raw_results or []:
                    title = str(item.get("title") or "").strip()
                    url = str(item.get("href") or "").strip()
                    snippet = str(item.get("body") or "").strip()

                    if not title or not url or not url.startswith("https://"):
                        continue

                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    results.append(
                        SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                        )
                    )

                logger.info(
                    "Web search returned %s results for query.",
                    len(results),
                )

                return results

        except Exception as exc:
            logger.warning(
                "DuckDuckGo search failed: %s",
                type(exc).__name__,
            )

            raise RuntimeError(
                "Web search temporarily failed. "
                "Check your internet connection or search provider."
            ) from None