import pytest

from tools.search.factory import create_search_provider
from tools.search.duckduckgo import DuckDuckGoSearchProvider
from tools.search.mock import MockSearchProvider


def test_create_mock_provider():
    provider = create_search_provider("mock")

    assert isinstance(provider, MockSearchProvider)


def test_create_duckduckgo_provider():
    provider = create_search_provider("duckduckgo")

    assert isinstance(provider, DuckDuckGoSearchProvider)


def test_provider_name_is_case_insensitive():
    provider = create_search_provider("MOCK")

    assert isinstance(provider, MockSearchProvider)


def test_provider_name_ignores_surrounding_spaces():
    provider = create_search_provider("  mock  ")

    assert isinstance(provider, MockSearchProvider)


@pytest.mark.parametrize("provider_name", ["", " ", "\n"])
def test_empty_provider_name_raises_error(provider_name):
    with pytest.raises(ValueError, match="cannot be empty"):
        create_search_provider(provider_name)


def test_unsupported_provider_raises_error():
    with pytest.raises(ValueError, match="Unsupported search provider"):
        create_search_provider("unknown")