"""
Retry mechanisms and circuit breaker patterns for resilient error handling.

This module provides decorators and utilities for implementing retry logic
and circuit breaker patterns to handle transient failures gracefully.
"""

import asyncio
from collections.abc import Callable
from enum import Enum
from functools import wraps
import time
from typing import Any, TypeVar

from src.agentic_crypto_influencer.config.app_constants import (
    COMPONENT_CIRCUIT_BREAKER,
    COMPONENT_RETRY,
)
from src.agentic_crypto_influencer.config.error_constants import ERROR_VALIDATION_GENERAL
from src.agentic_crypto_influencer.config.logging_config import get_logger
from src.agentic_crypto_influencer.error_management.exceptions import (
    APIConnectionError,
    RateLimitError,
    RetryableError,
    get_retry_delay,
    is_retryable_error,
)

logger = get_logger(f"{COMPONENT_RETRY}.{COMPONENT_RETRY}")

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against cascading failures.

    The circuit breaker monitors failures and opens when a threshold is reached,
    preventing further calls to a failing service for a specified time period.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        success_threshold: int = 3,
        service_name: str = "unknown",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Time to wait before attempting to close circuit (seconds)
            success_threshold: Number of successes needed to close circuit in half-open state
            service_name: Name of the service for logging
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.success_threshold = success_threshold
        self.service_name = service_name

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED

        self.logger = get_logger(f"{COMPONENT_CIRCUIT_BREAKER}.{service_name}")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        return (
            self.state == CircuitState.OPEN
            and self.last_failure_time is not None
            and time.time() - self.last_failure_time >= self.reset_timeout
        )

    def _record_success(self) -> None:
        """Record a successful operation."""
        self.failure_count = 0
        self.last_failure_time = None

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.logger.info(
                    f"Circuit breaker for {self.service_name} closed after successful recovery"
                )
        elif self.state == CircuitState.CLOSED:
            self.success_count = 0

    def _record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"Circuit breaker for {self.service_name} "
                f"opened after {self.failure_count} failures"
            )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"Circuit breaker for {self.service_name} "
                f"re-opened due to failure in half-open state"
            )

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info(
                    f"Circuit breaker for {self.service_name} entering half-open state"
                )
            else:
                raise APIConnectionError(
                    f"Circuit breaker is open for {self.service_name}",
                    service=self.service_name,
                    endpoint="circuit_breaker",
                    context={"state": self.state.value, "failure_count": self.failure_count},
                )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: type[Exception] | tuple[type[Exception], ...] | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to retry function calls on specified exceptions.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay on each retry
        exceptions: Exception types to retry on (None = retry on all exceptions)
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function
    """
    if exceptions is None:
        exceptions = (Exception,)
    elif not isinstance(exceptions, tuple):
        exceptions = (exceptions,)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Check if this error should be retried
                    if not is_retryable_error(e):
                        non_retryable_msg = (
                            f"Non-retryable error in {func.__name__}: {type(e).__name__}: {e}"
                        )
                        logger.warning(
                            non_retryable_msg,
                            extra={"attempt": attempt, "max_attempts": max_attempts},
                        )
                        raise

                    if attempt == max_attempts:
                        logger.error(
                            f"All retry attempts exhausted for {func.__name__}",
                            extra={
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "final_error": str(e),
                            },
                        )
                        raise

                    # Calculate delay (use error-specific delay if available)
                    retry_delay = get_retry_delay(e, attempt)
                    if retry_delay is None:
                        retry_delay = current_delay

                    retry_msg = (
                        f"Retrying {func.__name__} (attempt {attempt}/{max_attempts}) "
                        f"after {retry_delay:.1f}s"
                    )
                    logger.info(
                        retry_msg,
                        extra={
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": retry_delay,
                            "error": str(e),
                        },
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(retry_delay)
                    current_delay *= backoff_factor

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore

    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: type[Exception] | tuple[type[Exception], ...] | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[F], F]:
    """
    Async version of the retry decorator.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay on each retry
        exceptions: Exception types to retry on (None = retry on all exceptions)
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated async function
    """
    if exceptions is None:
        exceptions = (Exception,)
    elif not isinstance(exceptions, tuple):
        exceptions = (exceptions,)

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Check if this error should be retried
                    if not is_retryable_error(e):
                        logger.warning(
                            f"Non-retryable error in {func.__name__}: {type(e).__name__}: {e}",
                            extra={"attempt": attempt, "max_attempts": max_attempts},
                        )
                        raise

                    if attempt == max_attempts:
                        logger.error(
                            f"All retry attempts exhausted for {func.__name__}",
                            extra={
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "final_error": str(e),
                            },
                        )
                        raise

                    # Calculate delay (use error-specific delay if available)
                    retry_delay = get_retry_delay(e, attempt)
                    if retry_delay is None:
                        retry_delay = current_delay

                    retry_msg = (
                        f"Retrying {func.__name__} (attempt {attempt}/{max_attempts}) "
                        f"after {retry_delay:.1f}s"
                    )
                    logger.info(
                        retry_msg,
                        extra={
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": retry_delay,
                            "error": str(e),
                        },
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    await asyncio.sleep(retry_delay)
                    current_delay *= backoff_factor

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore

    return decorator


class RetryManager:
    """
    Centralized retry management for different services.
    """

    def __init__(self) -> None:
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.logger = get_logger("retry_manager")

    def get_circuit_breaker(self, service: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker(service_name=service)
            self.logger.info(f"Created circuit breaker for service: {service}")

        return self.circuit_breakers[service]

    def call_with_circuit_breaker(
        self, service: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute function with circuit breaker protection."""
        circuit_breaker = self.get_circuit_breaker(service)
        return circuit_breaker.call(func, *args, **kwargs)

    def get_service_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all monitored services."""
        status = {}
        for service, breaker in self.circuit_breakers.items():
            status[service] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "success_count": breaker.success_count,
                "last_failure_time": breaker.last_failure_time,
            }
        return status


# Global retry manager instance
retry_manager = RetryManager()
