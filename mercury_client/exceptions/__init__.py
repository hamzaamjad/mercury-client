"""Mercury API exceptions."""

from mercury_client.exceptions.exceptions import (
    MercuryAPIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)

__all__ = [
    "MercuryAPIError",
    "AuthenticationError",
    "RateLimitError",
    "ServerError",
    "EngineOverloadedError",
]