"""
Exception classes for the GoetGevonden API wrapper.
"""


class GoetGevondenError(Exception):
    """Base exception for all GoetGevonden API errors."""

    pass


class APIError(GoetGevondenError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ConnectionError(GoetGevondenError):
    """Raised when unable to connect to the API."""

    pass


class TimeoutError(GoetGevondenError):
    """Raised when an API request times out."""

    pass


class NotFoundError(APIError):
    """Raised when a requested resource is not found (404)."""

    def __init__(self, message: str = "Resource not found", response: dict | None = None):
        super().__init__(message, status_code=404, response=response)


class ValidationError(GoetGevondenError):
    """Raised when request parameters fail validation."""

    pass
