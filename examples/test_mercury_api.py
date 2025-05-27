#!/usr/bin/env python3
"""Simple test script for Mercury API client."""

import os
from mercury_client import MercuryClient


def main():
    """Test basic Mercury API functionality."""
    # Get API key from environment
    api_key = os.environ.get("MERCURY_API_KEY")
    if not api_key:
        print("Error: MERCURY_API_KEY not set in environment")
        return
    
    # Create client
    client = MercuryClient(api_key=api_key)
    print(f"✓ Client initialized with API key: {api_key[:10]}...")
    
    # Test 1: Simple chat completion
    print("\n1. Testing simple chat completion:")
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": "What is 2+2?"}],
            model="mercury-coder-small",
            max_tokens=50
        )
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Tokens used: {response.usage.total_tokens}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Chat with system message
    print("\n2. Testing chat with system message:")
    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a Python expert."},
                {"role": "user", "content": "Write a one-line list comprehension to get even numbers from 0 to 10"}
            ],
            model="mercury-coder-small",
            max_tokens=100
        )
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Streaming response
    print("\n3. Testing streaming response:")
    try:
        stream = client.chat_completion_stream(
            messages=[{"role": "user", "content": "Count from 1 to 5"}],
            model="mercury-coder-small",
            max_tokens=50
        )
        print("   Streaming: ", end="", flush=True)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()  # New line after streaming
    except Exception as e:
        print(f"\n   Error: {e}")
    
    print("\n✓ All tests completed!")


if __name__ == "__main__":
    main() 