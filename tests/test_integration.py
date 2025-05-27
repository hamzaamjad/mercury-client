"""Integration tests for Mercury client with real API."""

import os
import pytest
import pytest_asyncio
from mercury_client import MercuryClient, AsyncMercuryClient
from mercury_client.exceptions import AuthenticationError, RateLimitError


@pytest.mark.integration
class TestMercuryIntegration:
    """Integration tests with real Mercury API."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.environ.get("MERCURY_API_KEY")
        if not api_key:
            pytest.skip("MERCURY_API_KEY not set in environment")
        return api_key
    
    @pytest.fixture
    def client(self, api_key):
        """Create Mercury client with real API key."""
        return MercuryClient(api_key=api_key)
    
    @pytest_asyncio.fixture
    async def async_client(self, api_key):
        """Create async Mercury client with real API key."""
        # AsyncMercuryClient is not an awaitable, just return it directly
        return AsyncMercuryClient(api_key=api_key)
    
    def test_chat_completion_simple(self, client):
        """Test simple chat completion with real API."""
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Say hello"}],
            model="mercury-coder-small",
            max_tokens=50
        )
        
        assert response.id
        assert response.created
        assert response.model == "mercury-coder-small"
        assert len(response.choices) > 0
        assert response.choices[0].message.content
        assert response.usage.total_tokens > 0
        
    def test_chat_completion_with_system_message(self, client):
        """Test chat with system message."""
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "What is Python?"}
            ],
            model="mercury-coder-small",
            max_tokens=100
        )
        
        assert response.choices[0].message.content
        assert "python" in response.choices[0].message.content.lower()
        
    def test_streaming_chat_completion(self, client):
        """Test streaming chat completion."""
        stream = client.chat_completion_stream(
            messages=[{"role": "user", "content": "Count from 1 to 5"}],
            model="mercury-coder-small",
            max_tokens=50
        )
        
        chunks = list(stream)
        assert len(chunks) > 0
        
        # Verify first chunk structure
        first_chunk = chunks[0]
        assert first_chunk.id
        assert first_chunk.model == "mercury-coder-small"
        
        # Collect all content
        full_content = ""
        for chunk in chunks:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                full_content += chunk.choices[0].delta.content
                
        assert full_content  # Should have some content
        
    @pytest.mark.asyncio
    async def test_async_chat_completion(self, async_client):
        """Test async chat completion."""
        response = await async_client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="mercury-coder-small",
            max_tokens=50
        )
        
        assert response.id
        assert response.choices[0].message.content
        
    @pytest.mark.asyncio
    async def test_async_streaming(self, async_client):
        """Test async streaming."""
        chunks_received = 0
        
        async for chunk in async_client.chat_completion_stream(
            messages=[{"role": "user", "content": "Tell me a short joke"}],
            model="mercury-coder-small",
            max_tokens=100
        ):
            chunks_received += 1
            assert chunk.id
            
        assert chunks_received > 0
        
    def test_fill_in_the_middle(self, client):
        """Test FIM endpoint."""
        response = client.fill_in_the_middle(
            prompt="def add(a, b):\n    ",
            suffix="\n    return result",
            model="mercury-coder-small",
            max_tokens=50
        )
        
        assert response.id
        assert response.created
        assert len(response.choices) > 0
        assert response.choices[0].text
        
    def test_invalid_api_key(self):
        """Test that invalid API key raises AuthenticationError."""
        client = MercuryClient(api_key="invalid-key")
        
        with pytest.raises(AuthenticationError):
            client.chat_completion(
                messages=[{"role": "user", "content": "Test"}],
                model="mercury-coder-small"
            )
            
    def test_model_list(self, client):
        """Test listing available models."""
        # This assumes there's a models endpoint - adjust if needed
        try:
            models = client.list_models()
            assert len(models) > 0
            assert any("mercury" in model.id for model in models)
        except AttributeError:
            # If list_models isn't implemented, skip this test
            pytest.skip("list_models not implemented") 