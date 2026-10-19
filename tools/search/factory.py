from core.config import get_settings
from tools.search.base import SearchProvider
from tools.search.duckduckgo import DuckDuckGoSearchProvider
from tools.search.mock import MockSearchProvider


def create_search_provider(
    provider_name: str | None = None,
) -> SearchProvider:
    """Create a search provider using explicit or configured settings."""

    if provider_name is None:
        provider_name = get_settings().search_provider

    if not provider_name or not provider_name.strip():
        raise ValueError("Search provider name cannot be empty.")

    provider_name = provider_name.strip().lower()

    if provider_name == "duckduckgo":
        return DuckDuckGoSearchProvider()

    if provider_name == "mock":
        return MockSearchProvider()

    raise ValueError(
        f"Unsupported search provider: {provider_name}"
    )