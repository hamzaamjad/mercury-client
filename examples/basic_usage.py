#!/usr/bin/env python3
"""Basic usage example for Mercury Client."""

import os
from mercury_client import MercuryClient

def main():
    # Initialize client (API key from environment or pass directly)
    client = MercuryClient()
    
    # Example 1: Simple chat completion
    print("=== Simple Chat Completion ===")
    response = client.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Write a Python function to calculate factorial"}
        ],
        model="mercury-coder-small",
        max_tokens=200
    )
    print(response.choices[0].message.content)
    print(f"\nTokens used: {response.usage.total_tokens}")
    
    # Example 2: Streaming chat completion
    print("\n=== Streaming Chat Completion ===")
    print("Assistant: ", end="", flush=True)
    for chunk in client.chat_completion_stream(
        messages=[
            {"role": "user", "content": "Explain recursion in one sentence"}
        ],
        max_tokens=100
    ):
        if chunk.choices[0].message.content:
            print(chunk.choices[0].message.content, end="", flush=True)
    print("\n")
    
    # Example 3: Fill-in-the-Middle completion
    print("=== Fill-in-the-Middle Completion ===")
    fim_response = client.fim_completion(
        prompt="def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    \n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    \n    # TODO: Implement merge logic here\n    ",
        suffix="\n    return result",
        max_tokens=150
    )
    print("Generated code:")
    print(fim_response.choices[0].text)
    
    # Clean up
    client.close()

if __name__ == "__main__":
    # Make sure to set INCEPTION_API_KEY environment variable
    # or pass api_key parameter to MercuryClient
    if not os.getenv("INCEPTION_API_KEY"):
        print("Please set INCEPTION_API_KEY environment variable")
        exit(1)
    
    main()