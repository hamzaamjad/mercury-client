"""Fill-in-the-Middle (FIM) completion models for Mercury API."""

from typing import Optional, List, Union, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class FIMCompletionRequest(BaseModel):
    """FIM completion request model."""
    
    model: str = Field(default="mercury-coder-small")
    prompt: str = Field(description="The prefix text before the cursor")
    suffix: Optional[str] = Field(default="", description="The suffix text after the cursor")
    max_tokens: Optional[int] = Field(default=10000, ge=1, le=32000)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=1.5, ge=-2.0, le=2.0)
    temperature: Optional[float] = Field(default=0.0, description="Only 0.0 is supported")
    stop: Optional[Union[str, List[str]]] = Field(default=None, max_length=4)
    stream: Optional[bool] = Field(default=False)
    
    model_config = ConfigDict(extra="allow")


class FIMChoice(BaseModel):
    """FIM completion choice."""
    
    index: int
    text: str
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class FIMCompletionResponse(BaseModel):
    """FIM completion response model."""
    
    id: str
    object: Literal["text_completion"] = "text_completion"
    created: int
    model: str
    choices: List[FIMChoice]
    usage: Optional["Usage"] = None
    
    model_config = ConfigDict(extra="allow")


# Import Usage from chat models to avoid duplication
from mercury_client.models.chat import Usage

# Update the forward reference
FIMCompletionResponse.model_rebuild()