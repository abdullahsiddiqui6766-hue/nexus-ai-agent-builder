from tools.search.base import SearchProvider, SearchResult


class MockSearchProvider(SearchProvider):
    """A predictable search provider for automated testing."""

    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.results = results or []
        self.last_query: str | None = None
        self.last_max_results: int | None = None

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """Return predefined results without accessing the internet."""

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not 1 <= max_results <= 10:
            raise ValueError("max_results must be between 1 and 10.")

        self.last_query = query.strip()
        self.last_max_results = max_results

        return self.results[:max_results]