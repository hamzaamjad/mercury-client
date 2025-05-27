"""Tests for Mercury client using pytest-httpx."""

import pytest
import httpx

from mercury_client import MercuryClient, AsyncMercuryClient
from mercury_client.exceptions import (
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)
from mercury_client.models import ChatCompletionResponse


class TestMercuryClientWithHTTPX:
    """Test synchronous Mercury client with httpx mocking."""

    def test_chat_completion_success(self, httpx_mock):
        """Test successful chat completion."""
        # Setup mock response
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677649420,
                "model": "mercury-coder-small",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 8,
                    "total_tokens": 18
                }
            },
            status_code=200
        )

        client = MercuryClient(api_key="test-key")
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert isinstance(response, ChatCompletionResponse)
        assert response.choices[0].message.content == "Hello! How can I help you?"
        assert response.usage.total_tokens == 18

        # Verify the request
        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Content-Type"] == "application/json"
        
    def test_streaming_chat_completion(self, httpx_mock):
        """Test streaming chat completion."""
        # Setup SSE stream response
        stream_data = [
            'data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1677649420, "model": "mercury-coder-small", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "Hello"}, "finish_reason": null}]}',
            'data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1677649420, "model": "mercury-coder-small", "choices": [{"index": 0, "delta": {"content": " world!"}, "finish_reason": null}]}',
            'data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1677649420, "model": "mercury-coder-small", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}',
            'data: [DONE]'
        ]
        
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            text="\n".join(stream_data),
            headers={"content-type": "text/event-stream"},
            status_code=200
        )

        client = MercuryClient(api_key="test-key")
        chunks = list(client.chat_completion_stream(
            messages=[{"role": "user", "content": "Hello"}]
        ))

        assert len(chunks) == 3
        assert chunks[0].choices[0].delta.content == "Hello"
        assert chunks[1].choices[0].delta.content == " world!"
        
    def test_authentication_error(self, httpx_mock):
        """Test authentication error handling."""
        # AuthenticationError (401) is not retried, so only one response needed
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={"error": {"message": "Incorrect API key"}},
            status_code=401
        )

        client = MercuryClient(api_key="invalid-key")
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.chat_completion(messages=[{"role": "user", "content": "Test"}])
            
        assert "Incorrect API key" in str(exc_info.value)
        
    def test_rate_limit_error_with_retry_after(self, httpx_mock):
        """Test rate limit error with Retry-After header."""
        # RateLimitError may be retried, so we need to mock multiple responses
        # Since it will fail all retries, we'll mock the same response multiple times
        for _ in range(4):  # Default is 3 retries + 1 initial attempt
            httpx_mock.add_response(
                method="POST",
                url="https://api.inceptionlabs.ai/v1/chat/completions",
                json={"error": {"message": "Rate limit exceeded"}},
                headers={"Retry-After": "60"},
                status_code=429
            )

        client = MercuryClient(api_key="test-key")
        
        with pytest.raises(RateLimitError) as exc_info:
            client.chat_completion(messages=[{"role": "user", "content": "Test"}])
            
        assert exc_info.value.retry_after == 60
        assert "Rate limit exceeded" in str(exc_info.value)
        
    def test_server_error(self, httpx_mock):
        """Test server error handling."""
        # ServerError (500) may be retried
        for _ in range(4):  # Default is 3 retries + 1 initial attempt
            httpx_mock.add_response(
                method="POST",
                url="https://api.inceptionlabs.ai/v1/chat/completions",
                json={"error": {"message": "Internal server error"}},
                status_code=500
            )

        client = MercuryClient(api_key="test-key")
        
        with pytest.raises(ServerError) as exc_info:
            client.chat_completion(messages=[{"role": "user", "content": "Test"}])
            
        assert "Internal server error" in str(exc_info.value)
        
    def test_engine_overloaded_error(self, httpx_mock):
        """Test engine overloaded error handling."""
        # EngineOverloadedError (503) is retried
        for _ in range(4):  # Default is 3 retries + 1 initial attempt
            httpx_mock.add_response(
                method="POST",
                url="https://api.inceptionlabs.ai/v1/chat/completions",
                json={"error": {"message": "Engine is overloaded"}},
                status_code=503
            )

        client = MercuryClient(api_key="test-key")
        
        with pytest.raises(EngineOverloadedError) as exc_info:
            client.chat_completion(messages=[{"role": "user", "content": "Test"}])
            
        assert "Engine is overloaded" in str(exc_info.value)
        
    def test_retry_on_transient_error(self, httpx_mock):
        """Test retry logic on transient errors."""
        # First request fails with 503
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            status_code=503
        )
        
        # Second request succeeds
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677649420,
                "model": "mercury-coder-small",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Success after retry"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
            },
            status_code=200
        )

        client = MercuryClient(api_key="test-key")
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Test retry"}]
        )

        assert response.choices[0].message.content == "Success after retry"
        assert len(httpx_mock.get_requests()) == 2  # Verify retry happened
        

@pytest.mark.asyncio
class TestAsyncMercuryClientWithHTTPX:
    """Test async Mercury client with httpx mocking."""

    async def test_async_chat_completion_success(self, httpx_mock):
        """Test successful async chat completion."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={
                "id": "chatcmpl-456",
                "object": "chat.completion",
                "created": 1677649420,
                "model": "mercury-coder-small",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Async response!"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
            },
            status_code=200
        )

        async with AsyncMercuryClient(api_key="test-key") as client:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Async test"}]
            )

            assert response.choices[0].message.content == "Async response!"
            assert response.usage.total_tokens == 8

    async def test_async_streaming(self, httpx_mock):
        """Test async streaming chat completion."""
        stream_data = [
            'data: {"id": "chatcmpl-789", "object": "chat.completion.chunk", "created": 1677649420, "model": "mercury-coder-small", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "Async"}, "finish_reason": null}]}',
            'data: {"id": "chatcmpl-789", "object": "chat.completion.chunk", "created": 1677649420, "model": "mercury-coder-small", "choices": [{"index": 0, "delta": {"content": " streaming!"}, "finish_reason": null}]}',
            'data: [DONE]'
        ]
        
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            text="\n".join(stream_data),
            headers={"content-type": "text/event-stream"},
            status_code=200
        )

        async with AsyncMercuryClient(api_key="test-key") as client:
            chunks = []
            async for chunk in client.chat_completion_stream(
                messages=[{"role": "user", "content": "Stream test"}]
            ):
                chunks.append(chunk)

            assert len(chunks) == 2
            assert chunks[0].choices[0].delta.content == "Async"
            assert chunks[1].choices[0].delta.content == " streaming!" 