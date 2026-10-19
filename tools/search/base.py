from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Represents a single web search result."""

    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_000)
    snippet: str = Field(default="", max_length=5_000)


class SearchProvider(ABC):
    """Common interface for all search providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Search the web and return structured results."""
        raise NotImplementedError