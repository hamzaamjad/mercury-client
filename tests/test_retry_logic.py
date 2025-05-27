"""Tests for retry logic and error handling."""

import time
import pytest
import httpx
from unittest.mock import patch

from mercury_client import MercuryClient
from mercury_client.utils.retry import RetryConfig, calculate_delay
from mercury_client.exceptions import (
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)


class TestRetryLogic:
    """Test retry configuration and behavior."""
    
    def test_retry_config_defaults(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert RateLimitError in config.retry_on
        assert ServerError in config.retry_on
        assert EngineOverloadedError in config.retry_on
        
    def test_retry_config_custom(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False
        )
        assert config.max_retries == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        
    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False
        )
        
        # Test exponential growth
        assert calculate_delay(0, config) == 1.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(2, config) == 4.0
        assert calculate_delay(3, config) == 8.0
        assert calculate_delay(4, config) == 16.0
        
        # Test max delay cap
        assert calculate_delay(10, config) == 60.0  # Capped at max_delay
        
    def test_calculate_delay_with_retry_after(self):
        """Test delay calculation with Retry-After header."""
        config = RetryConfig(initial_delay=1.0, jitter=False)
        
        # When retry_after is provided, it should be used
        assert calculate_delay(0, config, retry_after=30) == 30
        assert calculate_delay(5, config, retry_after=45) == 45
        
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            initial_delay=10.0,
            jitter=True
        )
        
        # With jitter, delay should be between 0 and base_delay * (1 + jitter_factor)
        # The implementation adds random jitter, so we need to check ranges
        for attempt in range(5):
            delay = calculate_delay(attempt, config)
            base_delay = 10.0 * (2.0 ** attempt)
            base_delay = min(base_delay, config.max_delay)
            # Jitter can add up to 100% more delay
            assert 0 <= delay <= base_delay * 2
            
    def test_retry_on_rate_limit(self, httpx_mock):
        """Test retry behavior on rate limit errors."""
        # Mock responses - first two fail with 429, third succeeds
        for i in range(2):
            httpx_mock.add_response(
                method="POST",
                url="https://api.inceptionlabs.ai/v1/chat/completions",
                json={"error": {"message": "Rate limit exceeded"}},
                headers={"Retry-After": "1"},
                status_code=429
            )
        
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={
                "id": "success",
                "object": "chat.completion",
                "created": 1677649420,
                "model": "mercury-coder-small",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Success!"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
            },
            status_code=200
        )
        
        # Use custom retry config with short delays for testing
        config = RetryConfig(
            initial_delay=0.1,
            max_delay=0.5,
            jitter=False
        )
        
        client = MercuryClient(api_key="test-key", retry_config=config)
        
        start_time = time.time()
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Test"}]
        )
        elapsed = time.time() - start_time
        
        assert response.choices[0].message.content == "Success!"
        assert len(httpx_mock.get_requests()) == 3  # Two failures + one success
        # Should have waited at least 2 seconds (2 retries with Retry-After: 1)
        assert elapsed >= 2.0
        
    def test_retry_on_server_error(self, httpx_mock):
        """Test retry on 500 server errors."""
        # First request fails with 500
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={"error": {"message": "Internal server error"}},
            status_code=500
        )
        
        # Second request succeeds
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={
                "id": "success",
                "object": "chat.completion",
                "created": 1677649420,
                "model": "mercury-coder-small",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Recovered!"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
            },
            status_code=200
        )
        
        config = RetryConfig(initial_delay=0.01, jitter=False)
        client = MercuryClient(api_key="test-key", retry_config=config)
        
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Test"}]
        )
        
        assert response.choices[0].message.content == "Recovered!"
        assert len(httpx_mock.get_requests()) == 2
        
    def test_no_retry_on_auth_error(self, httpx_mock):
        """Test that authentication errors are not retried."""
        # AuthenticationError is not retried, so only add one mock response
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={"error": {"message": "Invalid API key"}},
            status_code=401
        )
        
        client = MercuryClient(api_key="invalid-key")
        
        with pytest.raises(AuthenticationError):
            client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )
        
        # Should only make one request (no retries for auth errors)
        assert len(httpx_mock.get_requests()) == 1
        
    def test_max_retries_exceeded(self, httpx_mock):
        """Test behavior when max retries are exceeded."""
        # Add exactly max_retries + 1 responses (initial + retries)
        config = RetryConfig(max_retries=3, initial_delay=0.01, jitter=False)
        
        for _ in range(4):  # 1 initial + 3 retries
            httpx_mock.add_response(
                method="POST",
                url="https://api.inceptionlabs.ai/v1/chat/completions",
                json={"error": {"message": "Service overloaded"}},
                status_code=503
            )
        
        client = MercuryClient(api_key="test-key", retry_config=config)
        
        with pytest.raises(EngineOverloadedError):
            client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )
        
        # Should make initial request + 3 retries = 4 total
        assert len(httpx_mock.get_requests()) == 4
        
    def test_retry_with_timeout(self, httpx_mock):
        """Test retry behavior with request timeouts."""
        # First request times out
        httpx_mock.add_exception(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            exception=httpx.TimeoutException("Request timed out")
        )
        
        # Second request succeeds
        httpx_mock.add_response(
            method="POST",
            url="https://api.inceptionlabs.ai/v1/chat/completions",
            json={
                "id": "success",
                "object": "chat.completion",
                "created": 1677649420,
                "model": "mercury-coder-small",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Success after timeout!"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
            },
            status_code=200
        )
        
        config = RetryConfig(
            initial_delay=0.01,
            jitter=False,
            retry_on=(RateLimitError, ServerError, EngineOverloadedError, httpx.TimeoutException)
        )
        client = MercuryClient(api_key="test-key", retry_config=config, timeout=1.0)
        
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Test"}]
        )
        
        assert response.choices[0].message.content == "Success after timeout!"
        assert len(httpx_mock.get_requests()) == 2 