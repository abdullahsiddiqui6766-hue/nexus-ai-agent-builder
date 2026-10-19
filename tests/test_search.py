import pytest

from tools.search.base import SearchResult
from tools.search.mock import MockSearchProvider


@pytest.fixture
def sample_results():
    return [
        SearchResult(
            title="Python Official Website",
            url="https://www.python.org/",
            snippet="The official Python programming language website.",
        ),
        SearchResult(
            title="Streamlit Documentation",
            url="https://docs.streamlit.io/",
            snippet="Documentation for building Streamlit applications.",
        ),
    ]


def test_search_returns_predefined_results(sample_results):
    provider = MockSearchProvider(sample_results)

    results = provider.search("Python", max_results=5)

    assert len(results) == 2
    assert results[0].title == "Python Official Website"
    assert results[1].title == "Streamlit Documentation"


def test_search_respects_max_results(sample_results):
    provider = MockSearchProvider(sample_results)

    results = provider.search("Python", max_results=1)

    assert len(results) == 1


def test_search_records_query(sample_results):
    provider = MockSearchProvider(sample_results)

    provider.search("  Python agents  ", max_results=2)

    assert provider.last_query == "Python agents"
    assert provider.last_max_results == 2


@pytest.mark.parametrize("query", ["", " ", "\n"])
def test_empty_query_raises_error(query):
    provider = MockSearchProvider()

    with pytest.raises(ValueError, match="Search query cannot be empty"):
        provider.search(query)


@pytest.mark.parametrize("max_results", [0, -1, 11])
def test_invalid_max_results_raises_error(max_results):
    provider = MockSearchProvider()

    with pytest.raises(ValueError, match="max_results must be between 1 and 10"):
        provider.search("Python", max_results=max_results)


def test_search_returns_empty_list_without_results():
    provider = MockSearchProvider()

    assert provider.search("Python") == []


def test_search_result_rejects_empty_title():
    with pytest.raises(ValueError):
        SearchResult(title="", url="https://example.com")


def test_search_result_rejects_empty_url():
    with pytest.raises(ValueError):
        SearchResult(title="Example", url="")