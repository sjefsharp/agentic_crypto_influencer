"""
Tests for BitvavoHandler using pytest best practices.
"""

from unittest.mock import patch

import pytest
from src.agentic_crypto_influencer.tools.bitvavo_handler import BitvavoHandler, main


@pytest.fixture
def bitvavo_handler() -> BitvavoHandler:
    """BitvavoHandler instance with mocked client for testing."""
    handler = BitvavoHandler()
    # Use a simple mock to avoid AsyncMock warnings
    from unittest.mock import Mock

    handler.client = Mock()
    return handler


@pytest.mark.unit
def test_init(bitvavo_handler: BitvavoHandler) -> None:
    """Test BitvavoHandler initialization."""
    assert bitvavo_handler.client is not None


@pytest.mark.unit
def test_get_market_data_success(bitvavo_handler: BitvavoHandler) -> None:
    """Test successful market data retrieval."""
    expected_data = {"market": "BTC-EUR", "price": "50000"}
    bitvavo_handler.client.tickerPrice.return_value = expected_data

    result = bitvavo_handler.get_market_data("BTC-EUR")

    # Verify client method was called correctly
    bitvavo_handler.client.tickerPrice.assert_called_once_with({"market": "BTC-EUR"})

    # Verify return value
    assert result == expected_data


@pytest.mark.unit
def test_get_market_data_client_error(bitvavo_handler: BitvavoHandler) -> None:
    """Test market data retrieval with client error."""
    bitvavo_handler.client.tickerPrice.side_effect = Exception("API Error")

    # The method handles errors internally and returns None
    result = bitvavo_handler.get_market_data("BTC-EUR")
    assert result is None


@pytest.mark.unit
def test_get_market_data_different_market(bitvavo_handler: BitvavoHandler) -> None:
    """Test market data retrieval for different market."""
    expected_data = {"market": "ETH-EUR", "price": "3000"}
    bitvavo_handler.client.tickerPrice.return_value = expected_data

    result = bitvavo_handler.get_market_data("ETH-EUR")

    # Verify client method was called with correct market
    bitvavo_handler.client.tickerPrice.assert_called_once_with({"market": "ETH-EUR"})

    # Verify return value
    assert result == expected_data


@pytest.mark.unit
def test_main_success() -> None:
    """Test main function with successful market data retrieval."""
    # Mock the BitvavoHandler class
    from unittest.mock import Mock

    mock_handler = Mock()
    with (
        patch(
            "src.agentic_crypto_influencer.tools.bitvavo_handler.BitvavoHandler"
        ) as mock_handler_class,
        patch("src.agentic_crypto_influencer.tools.bitvavo_handler.get_logger") as mock_get_logger,
    ):
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_handler_class.return_value = mock_handler
        mock_handler.get_market_data.return_value = {
            "market": "BTC-USDC",
            "price": "50000",
        }

        # Call main function
        main()

        # Verify handler was created
        mock_handler_class.assert_called_once()

        # Verify get_market_data was called with correct market
        mock_handler.get_market_data.assert_called_once_with("BTC-USDC")

        # Verify logger was called with success message (check the second call)
        mock_logger.info.assert_any_call(
            "Market Data for BTC-USDC: {'market': 'BTC-USDC', 'price': '50000'}"
        )


@pytest.mark.unit
def test_main_error() -> None:
    """Test main function with error during market data retrieval."""
    # Mock the BitvavoHandler class
    from unittest.mock import Mock

    mock_handler = Mock()
    with (
        patch(
            "src.agentic_crypto_influencer.tools.bitvavo_handler.BitvavoHandler"
        ) as mock_handler_class,
        patch("src.agentic_crypto_influencer.tools.bitvavo_handler.get_logger") as mock_get_logger,
    ):
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_handler_class.return_value = mock_handler
        mock_handler.get_market_data.side_effect = RuntimeError(
            "Failed to fetch market data: API Error"
        )

        # Call main function
        main()

        # Verify handler was created
        mock_handler_class.assert_called_once()

        # Verify get_market_data was called with correct market
        mock_handler.get_market_data.assert_called_once_with("BTC-USDC")

        # Verify error message was logged
        mock_logger.error.assert_called_once_with(
            "Error fetching market data: Failed to fetch market data: API Error"
        )
