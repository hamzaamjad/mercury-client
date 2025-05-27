"""Chat completion models for Mercury API."""

from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict


class Message(BaseModel):
    """Chat message model."""
    
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List["ToolCall"]] = None
    tool_call_id: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class FunctionDefinition(BaseModel):
    """Function definition for tools."""
    
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]


class Tool(BaseModel):
    """Tool definition model."""
    
    type: Literal["function"] = "function"
    function: FunctionDefinition


class Function(BaseModel):
    """Function call details."""
    
    name: str
    arguments: str


class ToolCall(BaseModel):
    """Tool call model."""
    
    id: str
    type: Literal["function"] = "function"
    function: Function


class StreamOptions(BaseModel):
    """Stream options model."""
    
    include_usage: bool = False


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""
    
    model: str = Field(default="mercury-coder-small")
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=10000, ge=1, le=32000)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=1.5, ge=-2.0, le=2.0)
    temperature: Optional[float] = Field(default=0.0, description="Only 0.0 is supported")
    stop: Optional[Union[str, List[str]]] = Field(default=None, max_length=4)
    stream: Optional[bool] = Field(default=False)
    stream_options: Optional[StreamOptions] = None
    diffusing: Optional[bool] = Field(default=False)
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    
    model_config = ConfigDict(extra="allow")

class Usage(BaseModel):
    """Token usage information."""
    
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Delta(BaseModel):
    """Delta message for streaming responses."""
    
    role: Optional[Literal["system", "user", "assistant", "tool"]] = None
    content: Optional[str] = None
    tool_calls: Optional[List["ToolCall"]] = None
    
    model_config = ConfigDict(extra="allow")


class Choice(BaseModel):
    """Chat completion choice."""
    
    index: int
    message: Optional[Message] = None  # Present in non-streaming responses
    delta: Optional[Delta] = None       # Present in streaming responses
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class ChatCompletionResponse(BaseModel):
    """Chat completion response model."""
    
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"] = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")