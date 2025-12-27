"""Tests for the GoetGevonden client."""

import pytest
import responses

from goetgevonden import (
    GoetGevondenClient,
    APIError,
    ConnectionError,
    NotFoundError,
    SearchResult,
    AboutInfo,
    IndexRange,
    SortOrder,
)


class TestGoetGevondenClient:
    """Test suite for GoetGevondenClient."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return GoetGevondenClient()

    @responses.activate
    def test_get_about(self, client):
        """Test getting server information."""
        responses.add(
            responses.GET,
            "https://api.goetgevonden.nl/about",
            json={
                "appName": "Broccoli",
                "version": "0.40.2",
                "startedAt": "2024-01-01T00:00:00Z",
                "baseURI": "https://api.goetgevonden.nl",
                "hucLogLevel": "INFO",
            },
            status=200,
        )

        info = client.get_about()

        assert isinstance(info, AboutInfo)
        assert info.app_name == "Broccoli"
        assert info.version == "0.40.2"

    @responses.activate
    def test_list_projects(self, client):
        """Test listing available projects."""
        responses.add(
            responses.GET,
            "https://api.goetgevonden.nl/projects",
            json=["republic"],
            status=200,
        )

        projects = client.list_projects()

        assert projects == ["republic"]

    @responses.activate
    def test_search_text(self, client):
        """Test simple text search."""
        responses.add(
            responses.POST,
            "https://api.goetgevonden.nl/projects/republic/search",
            json={
                "total": {"value": 100, "relation": "eq"},
                "results": [
                    {"_id": "1", "textType": "handgeschreven"},
                ],
                "aggs": {},
            },
            status=200,
        )

        results = client.search_text("Amsterdam")

        assert isinstance(results, SearchResult)
        assert results.total == 100
        assert len(results.hits) == 1

    @responses.activate
    def test_search_with_date_range(self, client):
        """Test search with date range filter."""
        responses.add(
            responses.POST,
            "https://api.goetgevonden.nl/projects/republic/search",
            json={
                "total": {"value": 50, "relation": "eq"},
                "results": [],
                "aggs": {},
            },
            status=200,
        )

        results = client.search_by_date("1600", "1650", text="oorlog")

        assert results.total == 50

    @responses.activate
    def test_search_pagination(self, client):
        """Test search pagination parameters."""
        responses.add(
            responses.POST,
            "https://api.goetgevonden.nl/projects/republic/search",
            json={
                "total": {"value": 1000, "relation": "eq"},
                "results": [],
                "aggs": {},
            },
            status=200,
        )

        results = client.search(from_=20, size=10)

        # Check that pagination params were sent
        assert "from=20" in responses.calls[0].request.url
        assert "size=10" in responses.calls[0].request.url

    @responses.activate
    def test_not_found_error(self, client):
        """Test 404 response handling."""
        responses.add(
            responses.GET,
            "https://api.goetgevonden.nl/projects/nonexistent",
            status=404,
        )

        with pytest.raises(NotFoundError):
            client.get_project_body_types("nonexistent")

    @responses.activate
    def test_api_error(self, client):
        """Test API error response handling."""
        responses.add(
            responses.GET,
            "https://api.goetgevonden.nl/projects",
            json={"error": "Internal server error"},
            status=500,
        )

        with pytest.raises(APIError) as exc_info:
            client.list_projects()

        assert exc_info.value.status_code == 500

    def test_context_manager(self):
        """Test using client as context manager."""
        with GoetGevondenClient() as client:
            assert client is not None
        # Session should be closed after exiting context

    def test_validation_error_negative_from(self, client):
        """Test validation of negative from_ parameter."""
        from goetgevonden import ValidationError

        with pytest.raises(ValidationError):
            client.search(from_=-1)

    def test_validation_error_negative_size(self, client):
        """Test validation of negative size parameter."""
        from goetgevonden import ValidationError

        with pytest.raises(ValidationError):
            client.search(size=-1)


class TestModels:
    """Test suite for data models."""

    def test_index_range_to_dict(self):
        """Test IndexRange serialization."""
        range_ = IndexRange(name="date", from_value="1600", to_value="1650")
        result = range_.to_dict()

        assert result == {"name": "date", "from": "1600", "to": "1650"}

    def test_index_range_partial(self):
        """Test IndexRange with partial values."""
        range_ = IndexRange(name="date", from_value="1600")
        result = range_.to_dict()

        assert result == {"name": "date", "from": "1600"}
        assert "to" not in result

    def test_search_result_from_dict_broccoli_format(self):
        """Test SearchResult parsing with Broccoli API format."""
        data = {
            "total": {"value": 42, "relation": "eq"},
            "results": [{"_id": "1"}],
            "aggs": {"test": {}},
        }

        result = SearchResult.from_dict(data)

        assert result.total == 42
        assert len(result.hits) == 1
        assert result.aggregations == {"test": {}}

    def test_search_result_from_dict_elasticsearch_format(self):
        """Test SearchResult parsing with Elasticsearch format."""
        data = {
            "hits": {
                "total": {"value": 42},
                "hits": [{"_id": "1"}],
            },
            "aggregations": {"test": {}},
        }

        result = SearchResult.from_dict(data)

        assert result.total == 42
        assert len(result.hits) == 1
        assert result.aggregations == {"test": {}}

    def test_about_info_from_dict(self):
        """Test AboutInfo parsing."""
        data = {
            "appName": "Broccoli",
            "version": "1.0.0",
            "startedAt": "2024-01-01",
            "baseURI": "http://localhost",
            "hucLogLevel": "DEBUG",
        }

        info = AboutInfo.from_dict(data)

        assert info.app_name == "Broccoli"
        assert info.version == "1.0.0"
        assert info.huc_log_level == "DEBUG"
