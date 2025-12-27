"""
GoetGevonden API Wrapper

A Python client library for the GoetGevonden API, providing access to
De resoluties van de Staten-Generaal (Resolutions of the States-General
of the Dutch Republic).

Example:
    >>> from goetgevonden import GoetGevondenClient
    >>> client = GoetGevondenClient()
    >>> results = client.search_text("Amsterdam")
    >>> print(f"Found {results.total} results")
"""

from .client import GoetGevondenClient, create_client
from .exceptions import (
    APIError,
    ConnectionError,
    GoetGevondenError,
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
    ViewAnnoConstraint,
    ViewConfiguration,
    ViewScope,
)

__version__ = "0.1.0"
__author__ = "GoetGevonden Contributors"
__license__ = "MIT"

__all__ = [
    # Client
    "GoetGevondenClient",
    "create_client",
    # Models
    "AboutInfo",
    "Annotation",
    "IndexQuery",
    "IndexRange",
    "SearchResult",
    "SortOrder",
    "ViewAnnoConstraint",
    "ViewConfiguration",
    "ViewScope",
    # Exceptions
    "GoetGevondenError",
    "APIError",
    "ConnectionError",
    "TimeoutError",
    "NotFoundError",
    "ValidationError",
]
