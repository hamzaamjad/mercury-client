"""Retry logic with exponential backoff for Mercury API."""

import asyncio
import time
from dataclasses import dataclass
from typing import TypeVar, Callable, Awaitable, Optional, Tuple, Type
from functools import wraps
import random

from mercury_client.exceptions import (
    MercuryAPIError,
    RateLimitError,
    ServerError,
    EngineOverloadedError,
)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: Tuple[Type[Exception], ...] = (
        RateLimitError,
        ServerError,
        EngineOverloadedError,
    )


def calculate_delay(
    attempt: int,
    config: RetryConfig,
    retry_after: Optional[int] = None,
) -> float:
    """Calculate delay for next retry attempt.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        retry_after: Optional retry-after header value
        
    Returns:
        Delay in seconds
    """
    if retry_after is not None:
        return float(retry_after)
    
    delay = min(
        config.initial_delay * (config.exponential_base ** attempt),
        config.max_delay
    )
    
    if config.jitter:
        delay *= (0.5 + random.random())
    
    return delay


def retry_sync(config: Optional[RetryConfig] = None):
    """Decorator for synchronous retry logic.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(config.retry_on) as e:
                    last_exception = e
                    if attempt < config.max_retries:
                        retry_after = getattr(e, 'retry_after', None)
                        delay = calculate_delay(attempt, config, retry_after)
                        time.sleep(delay)
                        continue
                    raise
                except Exception:
                    raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def retry_async(config: Optional[RetryConfig] = None):
    """Decorator for asynchronous retry logic.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(config.retry_on) as e:
                    last_exception = e
                    if attempt < config.max_retries:
                        retry_after = getattr(e, 'retry_after', None)
                        delay = calculate_delay(attempt, config, retry_after)
                        await asyncio.sleep(delay)
                        continue
                    raise
                except Exception:
                    raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator