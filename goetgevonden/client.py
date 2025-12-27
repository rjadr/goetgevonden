"""
Main client for the GoetGevonden API.

This module provides a Python interface to the GoetGevonden API,
which gives access to De resoluties van de Staten-Generaal (Resolutions
of the States-General of the Dutch Republic).
"""

from typing import Any
from urllib.parse import urljoin

import requests

from .exceptions import (
    APIError,
    ConnectionError,
    NotFoundError,
    TimeoutError,
    ValidationError,
)
from .models import (
    AboutInfo,
    Annotation,
    IndexQuery,
    IndexRange,
    SearchResult,
    SortOrder,
    ViewConfiguration,
)


class GoetGevondenClient:
    """
    Client for interacting with the GoetGevonden API.

    This API provides access to the Republic project, containing
    De resoluties van de Staten-Generaal (Resolutions of the States-General).

    Example:
        >>> client = GoetGevondenClient()
        >>> projects = client.list_projects()
        >>> print(projects)
        ['republic']

        >>> results = client.search("republic", text="Amsterdam")
        >>> print(f"Found {results.total} results")
    """

    DEFAULT_BASE_URL = "https://api.goetgevonden.nl"
    DEFAULT_PROJECT = "republic"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 30,
        session: requests.Session | None = None,
    ):
        """
        Initialize the GoetGevonden client.

        Args:
            base_url: Base URL for the API. Defaults to https://api.goetgevonden.nl
            timeout: Request timeout in seconds. Defaults to 30.
            session: Optional requests Session for connection pooling.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> Any:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body for POST requests

        Returns:
            Parsed JSON response

        Raises:
            APIError: If the API returns an error response
            ConnectionError: If unable to connect to the API
            TimeoutError: If the request times out
            NotFoundError: If the resource is not found
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}") from e
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request to {url} timed out") from e

        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {endpoint}")

        if not response.ok:
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"message": response.text}
            raise APIError(
                f"API error: {response.status_code}",
                status_code=response.status_code,
                response=error_data,
            )

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            return response.text

    # =========================================================================
    # Server Information Endpoints
    # =========================================================================

    def get_about(self) -> AboutInfo:
        """
        Get basic server information.

        Returns:
            AboutInfo: Server information including app name, version, etc.

        Example:
            >>> client = GoetGevondenClient()
            >>> info = client.get_about()
            >>> print(f"Server version: {info.version}")
        """
        data = self._request("GET", "/about")
        return AboutInfo.from_dict(data)

    def get_home_page(self) -> str:
        """
        Get the server homepage HTML.

        Returns:
            str: HTML content of the homepage
        """
        url = urljoin(self.base_url + "/", "/")
        response = self._session.get(url, timeout=self.timeout)
        return response.text

    # =========================================================================
    # Project Endpoints
    # =========================================================================

    def list_projects(self) -> list[str]:
        """
        Get list of configured projects.

        Returns:
            list[str]: List of project IDs (e.g., ['republic'])

        Example:
            >>> client = GoetGevondenClient()
            >>> projects = client.list_projects()
            >>> print(projects)
            ['republic']
        """
        return self._request("GET", "/projects")

    def get_project_body_types(self, project_id: str = DEFAULT_PROJECT) -> Any:
        """
        Get distinct body types for a project.

        Args:
            project_id: Project identifier. Defaults to 'republic'.

        Returns:
            Body types configuration for the project

        Example:
            >>> client = GoetGevondenClient()
            >>> body_types = client.get_project_body_types("republic")
        """
        return self._request("GET", f"/projects/{project_id}")

    def get_views(self, project_id: str = DEFAULT_PROJECT) -> dict[str, ViewConfiguration]:
        """
        Get view configurations for a project.

        Args:
            project_id: Project identifier. Defaults to 'republic'.

        Returns:
            dict[str, ViewConfiguration]: Mapping of view names to configurations

        Example:
            >>> client = GoetGevondenClient()
            >>> views = client.get_views("republic")
            >>> for name, config in views.items():
            ...     print(f"{name}: {config.scope}")
        """
        data = self._request("GET", f"/projects/{project_id}/views")
        return {key: ViewConfiguration.from_dict(value) for key, value in data.items()}

    def get_annotations(
        self,
        body_id: str,
        project_id: str = DEFAULT_PROJECT,
        include_results: str | None = None,
        views: str | None = None,
        overlap_types: str | None = None,
        relative_to: str = "Origin",
    ) -> dict[str, Any]:
        """
        Get annotations for a specific body ID.

        Args:
            body_id: The body identifier to retrieve annotations for
            project_id: Project identifier. Defaults to 'republic'.
            include_results: Optional filter for included results
            views: Optional view filter
            overlap_types: Optional overlap types filter
            relative_to: Reference point for annotations. Defaults to 'Origin'.

        Returns:
            dict: Annotation data for the specified body

        Example:
            >>> client = GoetGevondenClient()
            >>> annotations = client.get_annotations("some-body-id", "republic")
        """
        params = {"relativeTo": relative_to}
        if include_results is not None:
            params["includeResults"] = include_results
        if views is not None:
            params["views"] = views
        if overlap_types is not None:
            params["overlapTypes"] = overlap_types

        return self._request("GET", f"/projects/{project_id}/{body_id}", params=params)

    # =========================================================================
    # Search Endpoints
    # =========================================================================

    def search(
        self,
        project_id: str = DEFAULT_PROJECT,
        text: str | None = None,
        terms: dict[str, Any] | None = None,
        date_range: IndexRange | None = None,
        value_range: IndexRange | None = None,
        aggregations: dict[str, dict[str, Any]] | None = None,
        index_name: str | None = None,
        from_: int = 0,
        size: int = 10,
        fragment_size: int = 100,
        sort_by: str = "_score",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> SearchResult:
        """
        Search the project index.

        Args:
            project_id: Project identifier. Defaults to 'republic'.
            text: Full-text search query
            terms: Term filters as a dictionary
            date_range: Date range filter
            value_range: Numeric range filter
            aggregations: Aggregation definitions
            index_name: Specific index to search
            from_: Starting offset for pagination. Defaults to 0.
            size: Number of results to return. Defaults to 10.
            fragment_size: Size of text fragments in highlights. Defaults to 100.
            sort_by: Field to sort by. Defaults to '_score'.
            sort_order: Sort direction. Defaults to DESC.

        Returns:
            SearchResult: Search results including hits and aggregations

        Raises:
            ValidationError: If search parameters are invalid

        Example:
            >>> client = GoetGevondenClient()
            >>> # Simple text search
            >>> results = client.search(text="Amsterdam")
            >>> print(f"Found {results.total} results")

            >>> # Search with date range
            >>> from goetgevonden import IndexRange
            >>> date_filter = IndexRange(name="date", from_value="1600", to_value="1650")
            >>> results = client.search(text="oorlog", date_range=date_filter)

            >>> # Paginated search
            >>> results = client.search(text="Holland", from_=20, size=10)
        """
        if from_ < 0:
            raise ValidationError("'from_' must be non-negative")
        if size < 0:
            raise ValidationError("'size' must be non-negative")

        query = IndexQuery(
            text=text,
            terms=terms,
            date=date_range,
            range=value_range,
            aggs=aggregations,
        )

        params = {
            "from": from_,
            "size": size,
            "fragmentSize": fragment_size,
            "sortBy": sort_by,
            "sortOrder": sort_order.value,
        }
        if index_name is not None:
            params["indexName"] = index_name

        data = self._request(
            "POST",
            f"/projects/{project_id}/search",
            params=params,
            json=query.to_dict(),
        )
        return SearchResult.from_dict(data)

    def search_text(
        self,
        query: str,
        project_id: str = DEFAULT_PROJECT,
        from_: int = 0,
        size: int = 10,
    ) -> SearchResult:
        """
        Convenience method for simple text search.

        Args:
            query: Search query text
            project_id: Project identifier. Defaults to 'republic'.
            from_: Starting offset for pagination. Defaults to 0.
            size: Number of results to return. Defaults to 10.

        Returns:
            SearchResult: Search results

        Example:
            >>> client = GoetGevondenClient()
            >>> results = client.search_text("Staten-Generaal")
            >>> for hit in results.hits:
            ...     print(hit.get("_source", {}).get("title"))
        """
        return self.search(
            project_id=project_id,
            text=query,
            from_=from_,
            size=size,
        )

    def search_by_date(
        self,
        start_date: str,
        end_date: str,
        text: str | None = None,
        date_field: str = "date",
        project_id: str = DEFAULT_PROJECT,
        from_: int = 0,
        size: int = 10,
    ) -> SearchResult:
        """
        Search with a date range filter.

        Args:
            start_date: Start date (format depends on index configuration)
            end_date: End date
            text: Optional text query
            date_field: Name of the date field. Defaults to 'date'.
            project_id: Project identifier. Defaults to 'republic'.
            from_: Starting offset for pagination. Defaults to 0.
            size: Number of results to return. Defaults to 10.

        Returns:
            SearchResult: Search results within the date range

        Example:
            >>> client = GoetGevondenClient()
            >>> results = client.search_by_date("1600", "1610", text="Amsterdam")
        """
        date_range = IndexRange(name=date_field, from_value=start_date, to_value=end_date)
        return self.search(
            project_id=project_id,
            text=text,
            date_range=date_range,
            from_=from_,
            size=size,
        )

    # =========================================================================
    # Index Management Endpoints (Brinta)
    # =========================================================================

    def get_indices(self, project_id: str = DEFAULT_PROJECT) -> Any:
        """
        Get list of indices for a project.

        Args:
            project_id: Project identifier. Defaults to 'republic'.

        Returns:
            List of indices for the project

        Example:
            >>> client = GoetGevondenClient()
            >>> indices = client.get_indices("republic")
        """
        return self._request("GET", f"/brinta/{project_id}/indices")

    def create_index(self, index_name: str, project_id: str = DEFAULT_PROJECT) -> Any:
        """
        Create a new index.

        Note: This endpoint may require authentication/authorization.

        Args:
            index_name: Name of the index to create
            project_id: Project identifier. Defaults to 'republic'.

        Returns:
            Index creation response
        """
        return self._request("POST", f"/brinta/{project_id}/{index_name}")

    def delete_index(
        self,
        index_name: str,
        project_id: str = DEFAULT_PROJECT,
        delete_key: str | None = None,
    ) -> Any:
        """
        Delete an index.

        Note: This endpoint may require authentication/authorization.

        Args:
            index_name: Name of the index to delete
            project_id: Project identifier. Defaults to 'republic'.
            delete_key: Optional deletion key for authorization

        Returns:
            Index deletion response
        """
        params = {}
        if delete_key is not None:
            params["deleteKey"] = delete_key

        return self._request(
            "DELETE",
            f"/brinta/{project_id}/{index_name}",
            params=params if params else None,
        )

    def fill_index(
        self,
        index_name: str,
        project_id: str = DEFAULT_PROJECT,
        meta_anno: str | None = None,
        meta_values: str | None = None,
        take: int | None = None,
    ) -> Any:
        """
        Fill an index with data.

        Note: This endpoint may require authentication/authorization.

        Args:
            index_name: Name of the index to fill
            project_id: Project identifier. Defaults to 'republic'.
            meta_anno: Optional metadata annotation
            meta_values: Optional metadata values
            take: Optional limit on number of items to index

        Returns:
            Index fill response
        """
        params = {}
        if meta_anno is not None:
            params["metaAnno"] = meta_anno
        if meta_values is not None:
            params["metaValues"] = meta_values
        if take is not None:
            params["take"] = take

        return self._request(
            "POST",
            f"/brinta/{project_id}/{index_name}/fill",
            params=params if params else None,
        )

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    def __enter__(self) -> "GoetGevondenClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close session."""
        self.close()

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()


# Convenience function for quick access
def create_client(
    base_url: str = GoetGevondenClient.DEFAULT_BASE_URL,
    timeout: int = 30,
) -> GoetGevondenClient:
    """
    Create a new GoetGevonden client.

    Args:
        base_url: Base URL for the API
        timeout: Request timeout in seconds

    Returns:
        GoetGevondenClient: Configured client instance

    Example:
        >>> from goetgevonden import create_client
        >>> client = create_client()
        >>> results = client.search_text("Amsterdam")
    """
    return GoetGevondenClient(base_url=base_url, timeout=timeout)
