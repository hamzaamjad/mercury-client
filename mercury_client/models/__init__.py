"""Mercury API models."""

from mercury_client.models.chat import (
    Message,
    FunctionDefinition,
    Tool,
    Function,
    ToolCall,
    StreamOptions,
    ChatCompletionRequest,
    Usage,
    Choice,
    ChatCompletionResponse,
)
from mercury_client.models.fim import (
    FIMCompletionRequest,
    FIMChoice,
    FIMCompletionResponse,
)

__all__ = [
    # Chat models
    "Message",
    "FunctionDefinition",
    "Tool",
    "Function",
    "ToolCall",
    "StreamOptions",
    "ChatCompletionRequest",
    "Usage",
    "Choice",
    "ChatCompletionResponse",
    # FIM models
    "FIMCompletionRequest",
    "FIMChoice",
    "FIMCompletionResponse",
]