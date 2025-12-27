"""
Data models for the GoetGevonden API wrapper.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SortOrder(str, Enum):
    """Sort order for search results."""

    ASC = "ASC"
    DESC = "DESC"


class ViewScope(str, Enum):
    """Scope for view configurations."""

    OVERLAP = "OVERLAP"
    WITHIN = "WITHIN"


@dataclass
class AboutInfo:
    """Server information returned by the /about endpoint."""

    app_name: str
    version: str
    started_at: str
    base_uri: str
    huc_log_level: str

    @classmethod
    def from_dict(cls, data: dict) -> "AboutInfo":
        """Create an AboutInfo instance from API response data."""
        return cls(
            app_name=data.get("appName", ""),
            version=data.get("version", ""),
            started_at=data.get("startedAt", ""),
            base_uri=data.get("baseURI", ""),
            huc_log_level=data.get("hucLogLevel", ""),
        )


@dataclass
class ViewAnnoConstraint:
    """Annotation constraint for view configurations."""

    path: str
    value: str

    @classmethod
    def from_dict(cls, data: dict) -> "ViewAnnoConstraint":
        """Create a ViewAnnoConstraint instance from API response data."""
        return cls(
            path=data.get("path", ""),
            value=data.get("value", ""),
        )


@dataclass
class ViewConfiguration:
    """View configuration for a project."""

    anno: list[ViewAnnoConstraint]
    scope: ViewScope

    @classmethod
    def from_dict(cls, data: dict) -> "ViewConfiguration":
        """Create a ViewConfiguration instance from API response data."""
        return cls(
            anno=[ViewAnnoConstraint.from_dict(a) for a in data.get("anno", [])],
            scope=ViewScope(data.get("scope", "OVERLAP")),
        )


@dataclass
class IndexRange:
    """Range specification for index queries."""

    name: str
    from_value: str | None = None
    to_value: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API request."""
        result = {"name": self.name}
        if self.from_value is not None:
            result["from"] = self.from_value
        if self.to_value is not None:
            result["to"] = self.to_value
        return result


@dataclass
class IndexQuery:
    """Query parameters for searching an index."""

    text: str | None = None
    terms: dict[str, Any] | None = None
    date: IndexRange | None = None
    range: IndexRange | None = None
    aggs: dict[str, dict[str, Any]] | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API request."""
        result = {}
        if self.text is not None:
            result["text"] = self.text
        if self.terms is not None:
            result["terms"] = self.terms
        if self.date is not None:
            result["date"] = self.date.to_dict()
        if self.range is not None:
            result["range"] = self.range.to_dict()
        if self.aggs is not None:
            result["aggs"] = self.aggs
        return result


@dataclass
class SearchResult:
    """Search result from the API."""

    total: int
    hits: list[dict[str, Any]]
    aggregations: dict[str, Any] | None = None
    raw_response: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "SearchResult":
        """Create a SearchResult instance from API response data.

        Handles both Elasticsearch-style responses (with nested hits.hits)
        and the Broccoli API format (with top-level results and total).
        """
        # Try Broccoli API format first (top-level total and results)
        if "results" in data:
            total = data.get("total", 0)
            if isinstance(total, dict):
                total = total.get("value", 0)
            return cls(
                total=total,
                hits=data.get("results", []),
                aggregations=data.get("aggs"),
                raw_response=data,
            )

        # Fall back to Elasticsearch-style format
        hits_data = data.get("hits", {})
        total = hits_data.get("total", 0)
        if isinstance(total, dict):
            total = total.get("value", 0)

        return cls(
            total=total,
            hits=hits_data.get("hits", []),
            aggregations=data.get("aggregations"),
            raw_response=data,
        )


@dataclass
class Annotation:
    """Annotation data from the API."""

    body_id: str
    body_type: str
    annotations: list[dict[str, Any]]
    raw_response: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict, body_id: str = "") -> "Annotation":
        """Create an Annotation instance from API response data."""
        return cls(
            body_id=body_id or data.get("bodyId", ""),
            body_type=data.get("bodyType", ""),
            annotations=data.get("annotations", []),
            raw_response=data,
        )
