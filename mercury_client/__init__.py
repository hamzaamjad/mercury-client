"""Mercury Client - Python SDK for Inception Labs Mercury API.

A production-ready Python client library for the Mercury diffusion-LLM API,
providing both synchronous and asynchronous interfaces with full type safety.
"""

from mercury_client.client import MercuryClient
from mercury_client.async_client import AsyncMercuryClient
from mercury_client.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    FIMCompletionRequest,
    FIMCompletionResponse,
    Message,
    Tool,
    ToolCall,
)
from mercury_client.exceptions import (
    MercuryAPIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)

__version__ = "0.1.0"
__author__ = "Hamza Amjad"
__email__ = "hamza@example.com"

__all__ = [
    # Clients
    "MercuryClient",
    "AsyncMercuryClient",
    # Models
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "FIMCompletionRequest",
    "FIMCompletionResponse",
    "Message",
    "Tool",
    "ToolCall",
    # Exceptions
    "MercuryAPIError",
    "AuthenticationError",
    "RateLimitError",
    "ServerError",
    "EngineOverloadedError",
]