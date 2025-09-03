"""
Tests for ErrorManager using pytest best practices.
"""

from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager, main


@pytest.fixture  # type: ignore[misc]
def error_manager() -> ErrorManager:
    """ErrorManager instance for testing."""
    return ErrorManager()


@pytest.mark.unit  # type: ignore[misc]
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


@pytest.mark.unit  # type: ignore[misc]
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


@pytest.mark.unit  # type: ignore[misc]
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


@pytest.mark.unit  # type: ignore[misc]
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


@pytest.mark.unit  # type: ignore[misc]
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


@pytest.mark.unit  # type: ignore[misc]
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


@pytest.mark.unit  # type: ignore[misc]
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
