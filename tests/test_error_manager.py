"""
Tests for ErrorManager using pytest best practices.
"""

from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager, main
from src.agentic_crypto_influencer.error_management.exceptions import (
    APIConnectionError,
    APITimeoutError,
    ConfigurationError,
    ValidationError,
)


@pytest.fixture
def error_manager() -> ErrorManager:
    """ErrorManager instance for testing."""
    return ErrorManager()


@pytest.mark.unit
def test_handle_error(error_manager: ErrorManager) -> None:
    """Test error handling with ValueError."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ValueError("Test error")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logger.error.assert_called_once_with(
            "Error handled: ValueError: Test error",
            exc_info=True,
            extra={"error_type": "ValueError", "error_message": "Test error"},
        )

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_error_with_different_exception(error_manager: ErrorManager) -> None:
    """Test error handling with RuntimeError."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = RuntimeError("Runtime test error")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logger.error.assert_called_once_with(
            "Error handled: RuntimeError: Runtime test error",
            exc_info=True,
            extra={"error_type": "RuntimeError", "error_message": "Runtime test error"},
        )

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_error_with_custom_exception(error_manager: ErrorManager) -> None:
    """Test error handling with ConnectionError."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ConnectionError("Connection failed")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logger.error.assert_called_once_with(
            "Error handled: ConnectionError: Connection failed",
            exc_info=True,
            extra={"error_type": "ConnectionError", "error_message": "Connection failed"},
        )

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_error_with_exception_chaining(error_manager: ErrorManager) -> None:
    """Test error handling with chained exceptions."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        try:
            raise ValueError("Original error")
        except ValueError as original_error:
            chained_error = RuntimeError("Chained error")
            chained_error.__cause__ = original_error
            result = error_manager.handle_error(chained_error)

            # Verify logging was called
            mock_logger.error.assert_called_once_with(
                "Error handled: RuntimeError: Chained error",
                exc_info=True,
                extra={"error_type": "RuntimeError", "error_message": "Chained error"},
            )

            # Verify return value
            assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_error_with_empty_message(error_manager: ErrorManager) -> None:
    """Test error handling with empty exception message."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ValueError("")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logger.error.assert_called_once_with(
            "Error handled: ValueError: ",
            exc_info=True,
            extra={"error_type": "ValueError", "error_message": ""},
        )

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_error_with_none_exception(error_manager: ErrorManager) -> None:
    """Test error handling with None as exception (edge case)."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # This should not happen in practice, but testing edge case
        result = error_manager.handle_error(None)  # type: ignore[arg-type]

        # Verify logging was called
        mock_logger.error.assert_called_once_with(
            "Error handled: NoneType: None",
            exc_info=True,
            extra={"error_type": "NoneType", "error_message": "None"},
        )

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_main_function() -> None:
    """Test the main function that demonstrates error handling."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        main()

        # Verify that an error was logged
        mock_logger.error.assert_called_once_with(
            "Error handled: ValueError: Sample error message",
            exc_info=True,
            extra={
                "error_type": "ValueError",
                "error_message": "Sample error message",
                "demo": True,
                "function": "main",
            },
        )

        # Verify print was called with the user message (not needed since it's not printed)
        # The main function doesn't actually print the result, it just processes it


# Additional comprehensive tests for error manager specific methods
@pytest.mark.unit
def test_handle_configuration_error(error_manager: ErrorManager) -> None:
    """Test handling of ConfigurationError."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ConfigurationError("Missing API key", missing_config="API_KEY")
        context = "API Setup"
        result = error_manager.handle_configuration_error(error, context)

        mock_logger.error.assert_called_once_with(
            "Error handled: ConfigurationError: ConfigurationError: Missing API key",
            exc_info=True,
            extra={
                "error_type": "ConfigurationError",
                "error_message": "ConfigurationError: Missing API key",
                "config_name": context,
                "expected_type": None,
                "error_category": "configuration",
            },
        )
        assert result == f"Configuration error: {context}. Please check your settings."


@pytest.mark.unit
def test_handle_validation_error(error_manager: ErrorManager) -> None:
    """Test handling of ValidationError."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ValidationError("Invalid input format", field="email", value="invalid-email")
        result = error_manager.handle_validation_error(error, field="email", value="invalid-email")

        mock_logger.error.assert_called_once_with(
            "Error handled: ValidationError: ValidationError: Invalid input format",
            exc_info=True,
            extra={
                "error_type": "ValidationError",
                "error_message": "ValidationError: Invalid input format",
                "field": "email",
                "value": "invalid-email",
                "error_category": "validation",
            },
        )
        assert result == "Invalid email. Please check your input and try again."


@pytest.mark.unit
def test_handle_api_error_connection(error_manager: ErrorManager) -> None:
    """Test handling of API connection errors."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = APIConnectionError(
            "Failed to connect to API", service="twitter", endpoint="/api/v2/tweets"
        )
        result = error_manager.handle_api_error(
            error, service="twitter", endpoint="/api/v2/tweets"
        )

        mock_logger.error.assert_called_once_with(
            "Error handled: APIConnectionError: APIConnectionError: Failed to connect to API",
            exc_info=True,
            extra={
                "error_type": "APIConnectionError",
                "error_message": "APIConnectionError: Failed to connect to API",
                "service": "twitter",
                "endpoint": "/api/v2/tweets",
                "status_code": None,
            },
        )
        assert result == "Service temporarily unavailable (twitter). Please try again later."


@pytest.mark.unit
def test_handle_api_error_timeout(error_manager: ErrorManager) -> None:
    """Test handling of API timeout errors."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = APITimeoutError(
            "Request timed out", service="twitter", endpoint="/api/v2/tweets", timeout=30.0
        )
        result = error_manager.handle_api_error(
            error, service="twitter", endpoint="/api/v2/tweets", status_code=408
        )

        mock_logger.error.assert_called_once_with(
            "Error handled: APITimeoutError: APITimeoutError: Request timed out",
            exc_info=True,
            extra={
                "error_type": "APITimeoutError",
                "error_message": "APITimeoutError: Request timed out",
                "service": "twitter",
                "endpoint": "/api/v2/tweets",
                "status_code": 408,
            },
        )
        assert result == "Service temporarily unavailable (twitter). Please try again later."


@pytest.mark.unit
def test_handle_error_with_context(error_manager: ErrorManager) -> None:
    """Test error handling with additional context."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ValueError("Test error with context")
        context = {"module": "test_module", "function": "test_function"}
        result = error_manager.handle_error(error, context)

        mock_logger.error.assert_called_once_with(
            "Error handled: ValueError: Test error with context",
            exc_info=True,
            extra={
                "error_type": "ValueError",
                "error_message": "Test error with context",
                "module": "test_module",
                "function": "test_function",
            },
        )
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_unknown_exception_type(error_manager: ErrorManager) -> None:
    """Test handling of unknown exception types."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create a custom exception that's not in our known types
        class CustomError(Exception):
            pass

        error = CustomError("Unknown error type")
        result = error_manager.handle_error(error)

        mock_logger.error.assert_called_once_with(
            "Error handled: CustomError: Unknown error type",
            exc_info=True,
            extra={"error_type": "CustomError", "error_message": "Unknown error type"},
        )
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_handle_connection_error(error_manager: ErrorManager) -> None:
    """Test handling connection errors."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ConnectionError("Connection failed")
        result = error_manager.handle_connection_error(error, service="test_service")

        mock_logger.error.assert_called_once()
        assert "connection" in result.lower()


@pytest.mark.unit
def test_handle_workflow_error(error_manager: ErrorManager) -> None:
    """Test handling workflow errors."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = RuntimeError("Workflow failed")
        result = error_manager.handle_workflow_error(error, workflow_step="test_step")

        mock_logger.error.assert_called_once()
        assert "workflow" in result.lower()


@pytest.mark.unit
def test_handle_data_processing_error(error_manager: ErrorManager) -> None:
    """Test handling data processing errors."""
    with patch(
        "src.agentic_crypto_influencer.config.logging_config.get_logger"
    ) as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        error = ValueError("Invalid data")
        result = error_manager.handle_data_processing_error(
            error, data_type="json", operation="parse"
        )

        mock_logger.error.assert_called_once()
        assert "data" in result.lower() or "processing" in result.lower()


@pytest.mark.unit
def test_create_specific_error(error_manager: ErrorManager) -> None:
    """Test creating specific error types."""
    error = ValueError("Test error")

    # Test creating API error
    api_error = error_manager.create_specific_error(error, error_type="api")
    assert isinstance(api_error, Exception)

    # Test creating validation error
    validation_error = error_manager.create_specific_error(error, error_type="validation")
    assert isinstance(validation_error, Exception)


@pytest.mark.unit
def test_get_circuit_breaker_status(error_manager: ErrorManager) -> None:
    """Test getting circuit breaker status."""
    status = error_manager.get_circuit_breaker_status()

    assert isinstance(status, dict)
    assert "circuit_breakers" in status


@pytest.mark.unit
def test_call_with_circuit_breaker_success(error_manager: ErrorManager) -> None:
    """Test successful call with circuit breaker."""

    def test_function() -> str:
        return "success"

    result = error_manager.call_with_circuit_breaker("test_service_success", test_function)

    assert result == "success"


@pytest.mark.unit
def test_call_with_circuit_breaker_failure(error_manager: ErrorManager) -> None:
    """Test failed call with circuit breaker."""

    def failing_function() -> None:
        raise ValueError("Test failure")

    with pytest.raises(ValueError, match="Test failure"):
        error_manager.call_with_circuit_breaker("test_service_failure", failing_function)
