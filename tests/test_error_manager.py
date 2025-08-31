"""
Tests for ErrorManager using pytest best practices.
"""

from unittest.mock import patch

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
        "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
    ) as mock_logging_error:
        error = ValueError("Test error")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit  # type: ignore[misc]
def test_handle_error_with_different_exception(error_manager: ErrorManager) -> None:
    """Test error handling with RuntimeError."""
    with patch(
        "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
    ) as mock_logging_error:
        error = RuntimeError("Runtime error")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit  # type: ignore[misc]
def test_handle_error_with_custom_exception(error_manager: ErrorManager) -> None:
    """Test error handling with ConnectionError."""
    with patch(
        "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
    ) as mock_logging_error:
        error = ConnectionError("Network connection failed")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit  # type: ignore[misc]
def test_handle_error_with_exception_chaining(error_manager: ErrorManager) -> None:
    """Test error handling with chained exceptions."""
    with patch(
        "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
    ) as mock_logging_error:
        # Create a chained exception
        original_error = ValueError("Original error")
        chained_error = RuntimeError("Chained error")
        chained_error.__cause__ = original_error

        result = error_manager.handle_error(chained_error)

        # Verify logging was called
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit  # type: ignore[misc]
def test_handle_error_with_empty_message(error_manager: ErrorManager) -> None:
    """Test error handling with empty exception message."""
    with patch(
        "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
    ) as mock_logging_error:
        error = Exception("")
        result = error_manager.handle_error(error)

        # Verify logging was called
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit  # type: ignore[misc]
def test_handle_error_with_none_exception(error_manager: ErrorManager) -> None:
    """Test error handling with None as exception (edge case)."""
    with patch(
        "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
    ) as mock_logging_error:
        # Test with None passed as exception (edge case)
        result = error_manager.handle_error(None)  # type: ignore

        # Verify logging was called
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify return value
        assert result == "An unexpected error occurred. Please try again later."


@pytest.mark.unit  # type: ignore[misc]
def test_main_function() -> None:
    """Test the main function that demonstrates error handling."""
    with (
        patch(
            "src.agentic_crypto_influencer.error_management.error_manager.logging.error"
        ) as mock_logging_error,
        patch("builtins.print") as mock_print,
    ):
        # Call the main function
        main()

        # Verify that logging.error was called (from ErrorManager.handle_error)
        mock_logging_error.assert_called_once_with("An unexpected error occurred.", exc_info=True)

        # Verify that print was called with the error message
        mock_print.assert_called_once_with("An unexpected error occurred. Please try again later.")
