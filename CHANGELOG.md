# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-05-23

### Added
- Initial release of Mercury Client SDK
- Synchronous client (`MercuryClient`) with full API support
- Asynchronous client (`AsyncMercuryClient`) with full API support
- Chat completion endpoints with streaming support
- Fill-in-the-Middle (FIM) completion endpoints
- Automatic retry logic with exponential backoff and jitter
- Comprehensive error handling with typed exceptions
- Full type safety with Pydantic models
- Support for tool/function calling
- Environment variable support for API key
- Comprehensive documentation and examples
- Unit and integration test suite
- CI/CD workflow with GitHub Actions
- Python 3.8+ support

### Security
- API keys are never exposed in logs or error messages
- Secure handling of authentication headers
- Input validation for all API parameters

[0.1.0]: https://github.com/hamzaamjad/mercury-client/releases/tag/v0.1.0