"""Asynchronous client for Mercury API."""

import os
from typing import Optional, Dict, Any, AsyncIterator, Union
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv

from mercury_client.models.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
)
from mercury_client.models.fim import (
    FIMCompletionRequest,
    FIMCompletionResponse,
)
from mercury_client.exceptions import (
    MercuryAPIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)
from mercury_client.utils.retry import RetryConfig, calculate_delay

# Load environment variables
load_dotenv()


class AsyncMercuryClient:
    """Asynchronous client for Mercury API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.inceptionlabs.ai/v1",
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        """Initialize async Mercury client.
        
        Args:
            api_key: API key for authentication. If not provided, will look for
                MERCURY_API_KEY or INCEPTION_API_KEY environment variables.
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            retry_config: Configuration for retry behavior
        
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("MERCURY_API_KEY") or os.getenv("INCEPTION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set as MERCURY_API_KEY environment variable"
            )
        
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        
        # Configure httpx client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.timeout),
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _handle_response_errors(self, response: httpx.Response) -> None:
        """Handle API response errors.
        
        Args:
            response: HTTP response
            
        Raises:
            MercuryAPIError: If response indicates an error
        """
        if response.status_code >= 200 and response.status_code < 300:
            return
        
        try:
            error_data = response.json()
            message = error_data.get("error", {}).get("message", response.text)
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
        
        if response.status_code == 401:
            raise AuthenticationError(message)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None
            )
        elif response.status_code == 500:
            raise ServerError(message)
        elif response.status_code == 503:
            raise EngineOverloadedError(message)
        else:
            raise MercuryAPIError(
                message=message,
                status_code=response.status_code,
                response_data=error_data if 'error_data' in locals() else None
            )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            url: URL path
            **kwargs: Additional arguments for httpx request
            
        Returns:
            HTTP response
            
        Raises:
            MercuryAPIError: If request fails after retries
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self._client.request(method, url, **kwargs)
                self._handle_response_errors(response)
                return response
            except tuple(self.retry_config.retry_on) as e:
                last_exception = e
                if attempt < self.retry_config.max_retries:
                    retry_after = getattr(e, 'retry_after', None)
                    delay = calculate_delay(attempt, self.retry_config, retry_after)
                    import asyncio
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                raise

        if last_exception:
            raise last_exception

    async def chat_completion(
        self,
        messages: list[Union[Dict[str, Any], Message]],
        model: str = "mercury-coder-small",
        **kwargs
    ) -> ChatCompletionResponse:
        """Create a chat completion.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            **kwargs: Additional parameters for the request
            
        Returns:
            Chat completion response
        """
        # Convert dict messages to Message objects
        message_objs = []
        for msg in messages:
            if isinstance(msg, dict):
                message_objs.append(Message(**msg))
            else:
                message_objs.append(msg)
        
        request = ChatCompletionRequest(
            model=model,
            messages=message_objs,
            **kwargs
        )
        
        response = await self._request_with_retry(
            "POST",
            "/chat/completions",
            json=request.model_dump(exclude_none=True)
        )
        
        return ChatCompletionResponse(**response.json())

    async def chat_completion_stream(
        self,
        messages: list[Union[Dict[str, Any], Message]],
        model: str = "mercury-coder-small",
        **kwargs
    ) -> AsyncIterator[ChatCompletionResponse]:
        """Create a streaming chat completion.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            **kwargs: Additional parameters for the request
            
        Yields:
            Chat completion response chunks
        """
        # Convert dict messages to Message objects
        message_objs = []
        for msg in messages:
            if isinstance(msg, dict):
                message_objs.append(Message(**msg))
            else:
                message_objs.append(msg)
        
        request = ChatCompletionRequest(
            model=model,
            messages=message_objs,
            stream=True,
            **kwargs
        )
        
        async with self._client.stream(
            "POST",
            "/chat/completions",
            json=request.model_dump(exclude_none=True)
        ) as response:
            self._handle_response_errors(response)
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    
                    import json
                    try:
                        chunk = json.loads(data)
                        yield ChatCompletionResponse(**chunk)
                    except json.JSONDecodeError:
                        continue

    async def fim_completion(
        self,
        prompt: str,
        suffix: str = "",
        model: str = "mercury-coder-small",
        **kwargs
    ) -> FIMCompletionResponse:
        """Create a Fill-in-the-Middle completion.
        
        Args:
            prompt: The prefix text before the cursor
            suffix: The suffix text after the cursor
            model: Model to use for completion
            **kwargs: Additional parameters for the request
            
        Returns:
            FIM completion response
        """
        request = FIMCompletionRequest(
            model=model,
            prompt=prompt,
            suffix=suffix,
            **kwargs
        )
        
        response = await self._request_with_retry(
            "POST",
            "/fim/completions",
            json=request.model_dump(exclude_none=True)
        )
        
        return FIMCompletionResponse(**response.json())