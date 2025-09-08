"""
Tests for error_management.retry using pytest best practices.
"""

from datetime import UTC, datetime
import time

import pytest
from src.agentic_crypto_influencer.error_management.exceptions import (
    APIConnectionError,
    APITimeoutError,
    ValidationError,
)
from src.agentic_crypto_influencer.error_management.retry import (
    CircuitBreaker,
    CircuitState,
    retry,
    retry_manager,
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_init(self) -> None:
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(
            failure_threshold=3,
            reset_timeout=30.0,
            success_threshold=2,
            service_name="test_service",
        )

        assert cb.failure_threshold == 3
        assert cb.reset_timeout == 30.0
        assert cb.success_threshold == 2
        assert cb.service_name == "test_service"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_successful_call(self) -> None:
        """Test successful call through circuit breaker."""
        cb = CircuitBreaker()

        def test_func() -> str:
            return "success"

        result = cb.call(test_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_failure_below_threshold(self) -> None:
        """Test failure below threshold keeps circuit closed."""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        # First failure
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        # Second failure
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_opens_after_threshold(self) -> None:
        """Test circuit breaker opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        # First failure
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        # Second failure - should open circuit
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_rejects_when_open(self) -> None:
        """Test circuit breaker rejects calls when open."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=60.0)

        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        # Trigger circuit to open
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Should reject new calls
        def new_func() -> str:
            return "success"

        with pytest.raises(APIConnectionError) as exc_info:
            cb.call(new_func)

        assert "Circuit breaker is open" in str(exc_info.value)

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_half_open_transition(self) -> None:
        """Test transition to half-open state after timeout."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)

        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        # Trigger circuit to open
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for reset timeout
        time.sleep(0.2)

        def success_func() -> str:
            return "success"

        # Should transition to half-open and execute
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN  # type: ignore[comparison-overlap]

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_closes_after_success_threshold(self) -> None:
        """Test circuit breaker closes after success threshold in half-open."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1, success_threshold=2)

        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        # Open circuit
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        time.sleep(0.2)

        def success_func() -> str:
            return "success"

        # First success - should be half-open
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.success_count == 1

        # Second success - should close circuit
        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED  # type: ignore[comparison-overlap]
        assert cb.success_count == 0

    @pytest.mark.unit  # type: ignore[misc]
    def test_circuit_breaker_reopens_on_half_open_failure(self) -> None:
        """Test circuit breaker reopens on failure in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)

        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        # Open circuit
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        time.sleep(0.2)

        # Should transition to half-open, then fail and reopen
        with pytest.raises(APIConnectionError):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN


class TestRetryDecorator:
    """Test cases for retry decorator."""

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_successful_first_attempt(self) -> None:
        """Test retry decorator with successful first attempt."""

        @retry(max_attempts=3)
        def success_func() -> str:
            return "success"

        result = success_func()
        assert result == "success"

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_success_after_failures(self) -> None:
        """Test retry decorator succeeds after initial failures."""
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def eventually_success_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIConnectionError("Temporary failure", service="test", endpoint="/test")
            return "success"

        result = eventually_success_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_exhausts_attempts(self) -> None:
        """Test retry decorator exhausts all attempts."""

        @retry(max_attempts=2, delay=0.01)
        def always_fails() -> None:
            raise APIConnectionError("Always fails", service="test", endpoint="/test")

        with pytest.raises(APIConnectionError):
            always_fails()

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_non_retryable_error(self) -> None:
        """Test retry decorator doesn't retry non-retryable errors."""
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def validation_error_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ValidationError("Invalid input", field="test", value="invalid")

        with pytest.raises(ValidationError):
            validation_error_func()

        # Should only be called once (not retried)
        assert call_count == 1

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_specific_exceptions(self) -> None:
        """Test retry decorator with specific exception types."""

        @retry(max_attempts=3, delay=0.01, exceptions=APITimeoutError)
        def mixed_errors() -> None:
            raise APIConnectionError("Connection error", service="test", endpoint="/test")

        # Should not retry APIConnectionError when only APITimeoutError is specified
        with pytest.raises(APIConnectionError):
            mixed_errors()

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_with_callback(self) -> None:
        """Test retry decorator with on_retry callback."""
        retry_calls: list[tuple[str, int]] = []

        def on_retry_callback(exception: Exception, attempt: int) -> None:
            retry_calls.append((type(exception).__name__, attempt))

        @retry(max_attempts=3, delay=0.01, on_retry=on_retry_callback)
        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        with pytest.raises(APIConnectionError):
            failing_func()

        # Should have called callback for each retry
        assert len(retry_calls) == 2  # 3 attempts - 1 = 2 retries
        assert retry_calls[0] == ("APIConnectionError", 1)
        assert retry_calls[1] == ("APIConnectionError", 2)

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_backoff_delay(self) -> None:
        """Test retry decorator applies backoff delay."""
        start_time = datetime.now(UTC).timestamp()

        @retry(max_attempts=3, delay=0.1, backoff_factor=2.0)
        def failing_func() -> None:
            raise APIConnectionError("Test error", service="test", endpoint="/test")

        with pytest.raises(APIConnectionError):
            failing_func()

        # Should have some delay (but not exact due to timing variations)
        elapsed = datetime.now(UTC).timestamp() - start_time
        assert elapsed >= 0.2  # 0.1 + 0.2 (backoff) - some tolerance


class TestAsyncRetry:
    """Test cases for async retry decorator."""

    @pytest.mark.unit  # type: ignore[misc]
    def test_async_retry_import(self) -> None:
        """Test that async_retry can be imported."""
        from src.agentic_crypto_influencer.error_management.retry import async_retry

        assert async_retry is not None


class TestRetryManager:
    """Test cases for retry manager."""

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_manager_get_circuit_breaker(self) -> None:
        """Test retry manager creates and reuses circuit breakers."""
        cb1 = retry_manager.get_circuit_breaker("test_service")
        cb2 = retry_manager.get_circuit_breaker("test_service")

        # Should return the same instance
        assert cb1 is cb2
        assert cb1.service_name == "test_service"

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_manager_different_services(self) -> None:
        """Test retry manager creates different circuit breakers for different services."""
        cb1 = retry_manager.get_circuit_breaker("service1")
        cb2 = retry_manager.get_circuit_breaker("service2")

        # Should return different instances
        assert cb1 is not cb2
        assert cb1.service_name == "service1"
        assert cb2.service_name == "service2"

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_manager_execute_with_circuit_breaker(self) -> None:
        """Test retry manager executes function with circuit breaker."""

        def test_func() -> str:
            return "success"

        # Use a unique service name to avoid conflicts with other tests
        result = retry_manager.call_with_circuit_breaker("unique_test_service", test_func)
        assert result == "success"

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_manager_reset_circuit_breaker(self) -> None:
        """Test retry manager can reset circuit breaker."""
        # Get a circuit breaker and modify its state
        cb = retry_manager.get_circuit_breaker("test_service")
        cb.failure_count = 5
        cb.state = CircuitState.OPEN

        # Create a new circuit breaker (simulating reset)
        cb_new = retry_manager.get_circuit_breaker("new_test_service")

        # Should be in initial state
        assert cb_new.failure_count == 0
        assert cb_new.state == CircuitState.CLOSED

    @pytest.mark.unit  # type: ignore[misc]
    def test_retry_manager_get_service_status(self) -> None:
        """Test retry manager returns service status."""
        cb = retry_manager.get_circuit_breaker("test_service")
        cb.failure_count = 3
        cb.state = CircuitState.HALF_OPEN

        status = retry_manager.get_service_status()

        assert "test_service" in status
        assert status["test_service"]["state"] == "half_open"
        assert status["test_service"]["failure_count"] == 3
