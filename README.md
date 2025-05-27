# Mercury Client

![Test](https://github.com/hamzaamjad/mercury-client/workflows/Test/badge.svg)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Python SDK for the Inception Labs Mercury diffusion-LLM API, providing both synchronous and asynchronous interfaces with full type safety.

## Features

- 🚀 **Synchronous and Asynchronous Support** - Use `MercuryClient` or `AsyncMercuryClient` based on your needs
- 🔄 **Automatic Retry Logic** - Built-in exponential backoff with jitter for transient failures
- 🎭 **Full Type Safety** - Complete type hints and runtime validation with Pydantic
- 🌊 **Streaming Support** - Real-time streaming for chat completions
- 🛡️ **Robust Error Handling** - Typed exceptions for different error scenarios
- 🔧 **Flexible Configuration** - Customize timeouts, retries, and more
- 📝 **OpenAI-Compatible Interface** - Familiar API design for easy migration

## Installation

```bash
pip install mercury-client
```

Or install from source:

```bash
git clone https://github.com/hamzaamjad/mercury-client.git
cd mercury-client
pip install -e .
```

## Getting Started

### API Key Setup

First, obtain your API key from [Inception Labs](https://inceptionlabs.ai) and set it as an environment variable:

```bash
# Using export (Linux/macOS)
export MERCURY_API_KEY="sk_your_api_key_here"

# Using set (Windows)
set MERCURY_API_KEY=sk_your_api_key_here

# Or add to your shell profile (.bashrc, .zshrc, etc.)
echo 'export MERCURY_API_KEY="sk_your_api_key_here"' >> ~/.bashrc
```

Alternatively, you can pass the API key directly when initializing the client:

```python
from mercury_client import MercuryClient

client = MercuryClient(api_key="sk_your_api_key_here")
```

## Quick Start

### Basic Usage

```python
from mercury_client import MercuryClient

# Initialize the client (uses MERCURY_API_KEY env var by default)
client = MercuryClient()

# Create a chat completion
response = client.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is a diffusion model?"}
    ],
    model="mercury-coder-small"
)

print(response.choices[0].message.content)
```

### Async Usage

```python
import asyncio
from mercury_client import AsyncMercuryClient

async def main():
    async with AsyncMercuryClient() as client:
        response = await client.chat_completion(
            messages=[
                {"role": "user", "content": "Explain quantum computing"}
            ]
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

### Streaming Chat Completion

```python
# Synchronous streaming
for chunk in client.chat_completion_stream(
    messages=[{"role": "user", "content": "Write a story about AI"}],
    max_tokens=1000
):
    if chunk.choices[0].delta and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# Async streaming
async for chunk in client.chat_completion_stream(
    messages=[{"role": "user", "content": "Write a poem"}]
):
    if chunk.choices[0].delta and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Fill-in-the-Middle (FIM) Completion

```python
response = client.fim_completion(
    prompt="def fibonacci(",
    suffix="    return a + b",
    max_tokens=100
)

print(response.choices[0].text)
```

## Advanced Usage

### Custom Retry Configuration

```python
from mercury_client import MercuryClient, RetryConfig

retry_config = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

client = MercuryClient(
    api_key="your-api-key",
    retry_config=retry_config,
    timeout=60.0  # Request timeout in seconds
)
```

### Error Handling

```python
from mercury_client import MercuryClient
from mercury_client.exceptions import (
    AuthenticationError,
    RateLimitError,
    ServerError,
    EngineOverloadedError
)

try:
    response = client.chat_completion(
        messages=[{"role": "user", "content": "Hello"}]
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except EngineOverloadedError:
    print("Service is temporarily overloaded")
except ServerError:
    print("Server error occurred")
```

### Tool/Function Calling

```python
from mercury_client.models import Tool, FunctionDefinition

tools = [
    Tool(
        type="function",
        function=FunctionDefinition(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        )
    )
]

response = client.chat_completion(
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto"
)
```

## Configuration

### Environment Variables

- `MERCURY_API_KEY` - Your Mercury API key (primary)
- `INCEPTION_API_KEY` - Alternative environment variable (for backward compatibility)

### Client Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | `None` | API key for authentication |
| `base_url` | `str` | `https://api.inceptionlabs.ai/v1` | Base URL for the API |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `retry_config` | `RetryConfig` | Default config | Retry behavior configuration |

## API Reference

### MercuryClient / AsyncMercuryClient

#### Methods

- `chat_completion()` - Create a chat completion
- `chat_completion_stream()` - Create a streaming chat completion
- `fim_completion()` - Create a fill-in-the-middle completion (coming soon)
- `close()` - Close the HTTP client (also supports context manager)

### Models

All models are fully typed with Pydantic:

- `ChatCompletionRequest` / `ChatCompletionResponse`
- `FIMCompletionRequest` / `FIMCompletionResponse`
- `Message`, `Tool`, `ToolCall`, `Usage`, etc.

### Exceptions

- `MercuryAPIError` - Base exception for all API errors
- `AuthenticationError` - Invalid or missing API key (401)
- `RateLimitError` - Rate limit exceeded (429)
- `ServerError` - Server error (500)
- `EngineOverloadedError` - Service overloaded (503)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/hamzaamjad/mercury-client.git
cd mercury-client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mercury_client --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run integration tests (requires MERCURY_API_KEY)
pytest tests/test_integration.py -v -m integration
```

### Code Quality

```bash
# Format code
black mercury_client tests

# Sort imports
isort mercury_client tests

# Type checking
mypy mercury_client

# Linting
ruff mercury_client
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All tests pass
- Code is formatted with Black
- Type hints are added for new code
- Documentation is updated

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: hamza@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/hamzaamjad/mercury-client/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/hamzaamjad/mercury-client/discussions)