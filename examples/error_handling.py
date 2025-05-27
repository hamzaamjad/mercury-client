#!/usr/bin/env python3
"""Error handling examples for Mercury Client.

This example demonstrates best practices for handling various error scenarios
when using the Mercury API, including:
- Authentication errors
- Rate limiting with automatic retry
- Server errors with exponential backoff
- Network timeouts
- Graceful degradation
"""

import os
import time
import logging
from typing import Optional

from mercury_client import MercuryClient, AsyncMercuryClient
from mercury_client.exceptions import (
    MercuryAPIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)
from mercury_client.utils import RetryConfig

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_authentication_error():
    """Example: Handling authentication errors."""
    print("\n1. Handling Authentication Errors")
    print("-" * 40)
    
    # Try with invalid API key
    try:
        client = MercuryClient(api_key="invalid-key")
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        print("❌ Authentication failed - please check your API key")
        print("   Tip: Set MERCURY_API_KEY environment variable")
        return False
    
    return True


def handle_rate_limiting():
    """Example: Handling rate limits with retry."""
    print("\n2. Handling Rate Limits")
    print("-" * 40)
    
    client = MercuryClient()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.chat_completion(
                messages=[{"role": "user", "content": "Test rate limiting"}],
                max_tokens=50
            )
            print(f"✓ Success: {response.choices[0].message.content[:50]}...")
            return True
            
        except RateLimitError as e:
            retry_after = e.retry_after or 60  # Default to 60 seconds if not provided
            
            if attempt < max_retries - 1:
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                print(f"⏳ Rate limited - waiting {retry_after}s before retry {attempt + 2}/{max_retries}")
                time.sleep(retry_after)
            else:
                logger.error("Max retries exceeded for rate limit")
                print("❌ Rate limit persists after retries")
                return False
                
    return False


def handle_server_errors_with_backoff():
    """Example: Handle server errors with exponential backoff."""
    print("\n3. Handling Server Errors with Backoff")
    print("-" * 40)
    
    # Configure custom retry logic
    retry_config = RetryConfig(
        max_retries=5,
        initial_delay=1.0,
        max_delay=32.0,
        exponential_base=2.0,
        jitter=True  # Add randomness to prevent thundering herd
    )
    
    client = MercuryClient(retry_config=retry_config)
    
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Test with retry"}]
        )
        print(f"✓ Success: {response.choices[0].message.content[:50]}...")
        return True
        
    except (ServerError, EngineOverloadedError) as e:
        logger.error(f"Server error after all retries: {e}")
        print(f"❌ Server error persists: {e}")
        return False


def handle_timeout_with_fallback():
    """Example: Handle timeouts with fallback behavior."""
    print("\n4. Handling Timeouts with Fallback")
    print("-" * 40)
    
    # Create client with short timeout for demonstration
    client = MercuryClient(timeout=5.0)  # 5 second timeout
    
    try:
        # Try to get a response
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a very long story"}
            ],
            max_tokens=10  # Keep it short for demo
        )
        print(f"✓ Success: {response.choices[0].message.content[:50]}...")
        
    except Exception as e:
        logger.warning(f"Request failed: {e}")
        print("⚠️  Request failed - using fallback response")
        print("   Fallback: 'Service temporarily unavailable'")
        # In production, you might:
        # - Return cached response
        # - Use a simpler model
        # - Queue for later processing


def robust_streaming_example():
    """Example: Robust streaming with error recovery."""
    print("\n5. Robust Streaming with Error Recovery")
    print("-" * 40)
    
    client = MercuryClient()
    collected_content = []
    
    try:
        stream = client.chat_completion_stream(
            messages=[{"role": "user", "content": "Count from 1 to 10"}],
            max_tokens=100
        )
        
        print("Streaming: ", end="", flush=True)
        for chunk in stream:
            try:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        print(content, end="", flush=True)
                        collected_content.append(content)
                        
            except Exception as chunk_error:
                logger.warning(f"Error processing chunk: {chunk_error}")
                # Continue processing other chunks
                continue
                
        print("\n✓ Streaming completed")
        
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        print(f"\n⚠️  Streaming interrupted: {e}")
        if collected_content:
            print(f"   Partial response: {''.join(collected_content)}")


async def async_error_handling_example():
    """Example: Error handling with async client."""
    print("\n6. Async Error Handling")
    print("-" * 40)
    
    try:
        async with AsyncMercuryClient() as client:
            # Concurrent requests with error handling
            import asyncio
            
            async def make_request(prompt: str) -> Optional[str]:
                try:
                    response = await client.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=50
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Request failed for '{prompt}': {e}")
                    return None
            
            # Make multiple concurrent requests
            prompts = [
                "Say hello",
                "Say goodbye",
                "Count to 5"
            ]
            
            results = await asyncio.gather(
                *[make_request(p) for p in prompts],
                return_exceptions=True
            )
            
            # Process results
            for prompt, result in zip(prompts, results):
                if isinstance(result, Exception):
                    print(f"❌ '{prompt}' failed: {result}")
                elif result is None:
                    print(f"⚠️  '{prompt}' returned no result")
                else:
                    print(f"✓ '{prompt}': {result[:30]}...")
                    
    except Exception as e:
        logger.error(f"Async client error: {e}")
        print(f"❌ Async client error: {e}")


def comprehensive_error_handler():
    """Example: Comprehensive error handling wrapper."""
    print("\n7. Comprehensive Error Handler")
    print("-" * 40)
    
    def safe_completion(client: MercuryClient, messages: list, **kwargs) -> Optional[str]:
        """Safely make a completion request with full error handling."""
        try:
            response = client.chat_completion(messages=messages, **kwargs)
            return response.choices[0].message.content
            
        except AuthenticationError:
            logger.error("Authentication failed - check API key")
            return None
            
        except RateLimitError as e:
            wait_time = e.retry_after or 60
            logger.warning(f"Rate limited - retry after {wait_time}s")
            # In production: implement queue or retry logic
            return None
            
        except EngineOverloadedError:
            logger.warning("Engine overloaded - try simpler request")
            # Try with reduced tokens
            if kwargs.get('max_tokens', 0) > 100:
                kwargs['max_tokens'] = 100
                return safe_completion(client, messages, **kwargs)
            return None
            
        except ServerError:
            logger.error("Server error - service degraded")
            # In production: switch to backup service
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    # Example usage
    client = MercuryClient()
    result = safe_completion(
        client,
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        max_tokens=50
    )
    
    if result:
        print(f"✓ Response: {result}")
    else:
        print("❌ Failed to get response - check logs")


def main():
    """Run all error handling examples."""
    print("Mercury Client Error Handling Examples")
    print("=" * 50)
    
    # Check if API key is set
    if not os.environ.get("MERCURY_API_KEY"):
        print("⚠️  Warning: MERCURY_API_KEY not set")
        print("   Some examples may fail without a valid API key")
        print("   Set it with: export MERCURY_API_KEY='your-key-here'")
    
    # Run examples
    examples = [
        handle_authentication_error,
        handle_rate_limiting,
        handle_server_errors_with_backoff,
        handle_timeout_with_fallback,
        robust_streaming_example,
        comprehensive_error_handler,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            logger.error(f"Example {example.__name__} failed: {e}")
            print(f"❌ Example failed: {e}")
    
    # Run async example
    print("\nRunning async example...")
    import asyncio
    try:
        asyncio.run(async_error_handling_example())
    except Exception as e:
        logger.error(f"Async example failed: {e}")
        print(f"❌ Async example failed: {e}")
    
    print("\n" + "=" * 50)
    print("✓ Error handling examples completed")
    print("\nKey Takeaways:")
    print("- Always handle authentication errors explicitly")
    print("- Respect rate limits with exponential backoff")
    print("- Implement fallback strategies for failures")
    print("- Use custom retry configs for your use case")
    print("- Log errors for debugging and monitoring")


if __name__ == "__main__":
    main() 