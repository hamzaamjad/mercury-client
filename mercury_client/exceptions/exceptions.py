"""Exception classes for Mercury API errors."""

from typing import Optional, Dict, Any


class MercuryAPIError(Exception):
    """Base exception class for Mercury API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize Mercury API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Raw response data from API
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        """String representation of the error."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(MercuryAPIError):
    """Raised when API key is incorrect or missing (401)."""

    def __init__(self, message: str = "Incorrect API key provided") -> None:
        """Initialize authentication error."""
        super().__init__(message=message, status_code=401)


class RateLimitError(MercuryAPIError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit reached",
        retry_after: Optional[int] = None,
    ) -> None:
        """Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message=message, status_code=429)
        self.retry_after = retry_after


class ServerError(MercuryAPIError):
    """Raised when server encounters an error (500)."""

    def __init__(self, message: str = "Server error") -> None:
        """Initialize server error."""
        super().__init__(message=message, status_code=500)


class EngineOverloadedError(MercuryAPIError):
    """Raised when the engine is overloaded (503)."""

    def __init__(self, message: str = "Engine overloaded") -> None:
        """Initialize engine overloaded error."""
        super().__init__(message=message, status_code=503)