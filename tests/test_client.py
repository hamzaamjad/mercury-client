"""Tests for Mercury client."""

import pytest
import httpx
from unittest.mock import Mock, patch

from mercury_client import MercuryClient
from mercury_client.exceptions import (
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)
from mercury_client.models import ChatCompletionResponse, Message


class TestMercuryClient:
    """Test synchronous Mercury client."""

    def test_client_initialization(self):
        """Test client initialization with API key."""
        client = MercuryClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.inceptionlabs.ai/v1"
        
    def test_client_initialization_from_env(self, monkeypatch):
        """Test client initialization from environment variable."""
        # Clear any existing API keys
        monkeypatch.delenv("MERCURY_API_KEY", raising=False)
        monkeypatch.delenv("INCEPTION_API_KEY", raising=False)
        
        # Test with MERCURY_API_KEY (primary)
        monkeypatch.setenv("MERCURY_API_KEY", "mercury-test-key")
        client = MercuryClient()
        assert client.api_key == "mercury-test-key"
        
        # Test with INCEPTION_API_KEY (fallback)
        monkeypatch.delenv("MERCURY_API_KEY")
        monkeypatch.setenv("INCEPTION_API_KEY", "inception-test-key")
        client2 = MercuryClient()
        assert client2.api_key == "inception-test-key"
        
    def test_client_initialization_no_key(self, monkeypatch):
        """Test client initialization without API key raises error."""
        # Clear any existing API keys
        monkeypatch.delenv("MERCURY_API_KEY", raising=False)
        monkeypatch.delenv("INCEPTION_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="API key must be provided"):
            MercuryClient(api_key=None)
            
    def test_chat_completion_success(self):
        """Test successful chat completion."""
        client = MercuryClient(api_key="test-key")
        
        # Mock the HTTP response
        mock_response = {
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
        }
        
        with patch.object(client._client, 'request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: mock_response
            )
            
            response = client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            assert isinstance(response, ChatCompletionResponse)
            assert response.choices[0].message.content == "Hello! How can I help you?"
            assert response.usage.total_tokens == 18
            
    def test_authentication_error(self):
        """Test authentication error handling."""
        client = MercuryClient(api_key="invalid-key")
        
        with patch.object(client._client, 'request') as mock_request:
            mock_request.return_value = Mock(
                status_code=401,
                json=lambda: {"error": {"message": "Incorrect API key"}},
                text="Incorrect API key"
            )
            
            with pytest.raises(AuthenticationError):
                client.chat_completion(messages=[{"role": "user", "content": "Test"}])
                
    def test_rate_limit_error(self):
        """Test rate limit error handling."""
        client = MercuryClient(api_key="test-key")
        
        with patch.object(client._client, 'request') as mock_request:
            mock_request.return_value = Mock(
                status_code=429,
                json=lambda: {"error": {"message": "Rate limit exceeded"}},
                text="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )
            
            with pytest.raises(RateLimitError) as exc_info:
                client.chat_completion(messages=[{"role": "user", "content": "Test"}])
                
            assert exc_info.value.retry_after == 60