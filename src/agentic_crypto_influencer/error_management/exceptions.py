"""
Custom exception classes for the agentic crypto influencer system.

Provides specialized exceptions for different types of errors that can occur
during the execution of crypto trading agents and associated workflows.
"""

import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import override
else:
    try:
        from typing import override
    except ImportError:
        from typing import override


class AgenticCryptoError(Exception):
    """Base exception for all agentic crypto influencer related errors."""

    def __init__(
        self, message: str, error_code: str = "UNKNOWN", context: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    @override
    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}: {self.message}"


class ConfigurationError(AgenticCryptoError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        missing_config: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, "CONFIG_ERROR", context)
        self.missing_config = missing_config


class ValidationError(AgenticCryptoError):
    """Raised when input validation fails."""

    def __init__(
        self, message: str, field: str, value: Any, context: dict[str, Any] | None = None
    ):
        super().__init__(message, "VALIDATION_ERROR", context)
        self.field = field
        self.value = value


class APIError(AgenticCryptoError):
    """Base class for API-related errors."""

    def __init__(
        self,
        message: str,
        service: str,
        endpoint: str,
        status_code: int | None = None,
        error_code: str = "API_ERROR",
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, context)
        self.service = service
        self.endpoint = endpoint
        self.status_code = status_code


class APIConnectionError(APIError):
    """Raised when unable to connect to an API service."""

    def __init__(
        self, message: str, service: str, endpoint: str, context: dict[str, Any] | None = None
    ):
        super().__init__(message, service, endpoint, None, "API_CONNECTION_ERROR", context)


class APITimeoutError(APIError):
    """Raised when an API request times out."""

    def __init__(
        self,
        message: str,
        service: str,
        endpoint: str,
        timeout: float,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, service, endpoint, None, "API_TIMEOUT_ERROR", context)
        self.timeout = timeout


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        service: str,
        endpoint: str,
        retry_after: int | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, service, endpoint, 429, "API_RATE_LIMIT_ERROR", context)
        self.retry_after = retry_after


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""

    def __init__(
        self, message: str, service: str, endpoint: str, context: dict[str, Any] | None = None
    ):
        super().__init__(message, service, endpoint, 401, "API_AUTH_ERROR", context)


class DataProcessingError(AgenticCryptoError):
    """Raised when data processing fails."""

    def __init__(
        self, message: str, data_type: str, operation: str, context: dict[str, Any] | None = None
    ):
        super().__init__(message, "DATA_PROCESSING_ERROR", context)
        self.data_type = data_type
        self.operation = operation


class RedisConnectionError(AgenticCryptoError):
    """Raised when Redis connection fails."""

    def __init__(self, message: str, operation: str, context: dict[str, Any] | None = None):
        super().__init__(message, "REDIS_CONNECTION_ERROR", context)
        self.operation = operation


class WorkflowError(AgenticCryptoError):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, workflow_step: str, context: dict[str, Any] | None = None):
        super().__init__(message, "WORKFLOW_ERROR", context)
        self.workflow_step = workflow_step


class ExternalServiceError(AgenticCryptoError):
    """Raised when external service interaction fails."""

    def __init__(
        self, message: str, service: str, operation: str, context: dict[str, Any] | None = None
    ):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", context)
        self.service = service
        self.operation = operation


class RetryableError(AgenticCryptoError):
    """Base class for errors that can be retried."""

    def __init__(
        self,
        message: str,
        error_code: str = "RETRYABLE_ERROR",
        retry_after: float | None = None,
        max_retries: int = 3,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, context)
        self.retry_after = retry_after
        self.max_retries = max_retries


class NonRetryableError(AgenticCryptoError):
    """Base class for errors that should not be retried."""

    def __init__(
        self,
        message: str,
        error_code: str = "NON_RETRYABLE_ERROR",
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, context)


# Convenience function to determine if an error is retryable
def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable based on its type and characteristics.

    Args:
        error: The exception to check

    Returns:
        True if the error is retryable, False otherwise
    """
    # Direct retryable errors
    if isinstance(error, RetryableError):
        return True

    # Non-retryable errors
    if isinstance(error, NonRetryableError):
        return False

    # Specific API errors that are retryable
    if isinstance(error, APIConnectionError | APITimeoutError | APIRateLimitError):
        return True

    # Authentication errors are not retryable
    if isinstance(error, APIAuthenticationError):
        return False

    # Configuration and validation errors are not retryable
    if isinstance(error, ConfigurationError | ValidationError):
        return False

    # Redis connection errors are retryable
    return isinstance(error, RedisConnectionError)


def get_retry_delay(error: Exception, attempt: int) -> float:
    """
    Calculate appropriate retry delay for an error.

    Args:
        error: The exception that occurred
        attempt: Current attempt number (0-indexed)

    Returns:
        Delay in seconds before retry
    """
    # Check if error has retry_after attribute
    if hasattr(error, "retry_after") and error.retry_after is not None:
        retry_after = error.retry_after
        return float(retry_after) if retry_after is not None else 0.0

    # Check if error has retry_delay attribute
    if hasattr(error, "retry_delay") and error.retry_delay is not None:
        retry_delay = error.retry_delay
        return float(retry_delay) if retry_delay is not None else 0.0

    # Default exponential backoff with jitter
    base_delay = 2**attempt
    jitter = random.uniform(0.1, 0.5)  # Add 10-50% jitter  # nosec B311
    return float(base_delay + jitter)
