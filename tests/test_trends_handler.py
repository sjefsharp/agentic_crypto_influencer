import unittest
from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.trends_handler import TrendsHandler


class TestTrendsHandler:
    def test_init(self) -> None:
        """Test TrendsHandler initialization"""
        access_token = "test_token"
        handler = TrendsHandler(access_token)
        assert handler.access_token == access_token

    @patch("src.agentic_crypto_influencer.tools.trends_handler.requests.get")
    @patch("src.agentic_crypto_influencer.tools.trends_handler.logging.info")
    def test_get_personalized_trends_success(
        self, mock_logging_info: Mock, mock_requests_get: Mock
    ) -> None:
        """Test successful trends retrieval"""
        access_token = "test_token"
        handler = TrendsHandler(access_token)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"trends": ["trend1", "trend2"]}
        mock_requests_get.return_value = mock_response

        result = handler.get_personalized_trends("user123")

        # Verify request was made correctly
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert "Bearer test_token" in call_args[1]["headers"]["Authorization"]
        assert call_args[1]["timeout"] == 15

        # Verify logging
        mock_logging_info.assert_called_once_with("Trends response status: %d", 200)

        # Verify return value
        assert result == {"trends": ["trend1", "trend2"]}

    @patch("src.agentic_crypto_influencer.tools.trends_handler.requests.get")
    @patch("src.agentic_crypto_influencer.tools.trends_handler.logging.error")
    def test_get_personalized_trends_request_error(
        self, mock_logging_error: Mock, mock_requests_get: Mock
    ) -> None:
        """Test trends request with error response"""
        access_token = "test_token"
        handler = TrendsHandler(access_token)

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests_get.return_value = mock_response

        with pytest.raises(Exception, match="Trends request returned an error: 401") as exc_info:
            handler.get_personalized_trends("user123")

        mock_logging_error.assert_any_call("Trends request failed: %d %s", 401, "Unauthorized")
        mock_logging_error.assert_any_call(
            "Trends request error: %s",
            "Trends request returned an error: 401 Unauthorized",
        )
        assert "Trends request returned an error: 401" in str(exc_info.value)

    @patch("src.agentic_crypto_influencer.tools.trends_handler.requests.get")
    @patch("src.agentic_crypto_influencer.tools.trends_handler.logging.error")
    def test_get_personalized_trends_network_error(
        self, mock_logging_error: Mock, mock_requests_get: Mock
    ) -> None:
        """Test trends request with network error"""
        access_token = "test_token"
        handler = TrendsHandler(access_token)

        mock_requests_get.side_effect = Exception("Connection timeout")

        with pytest.raises(RuntimeError) as exc_info:
            handler.get_personalized_trends("user123")

        mock_logging_error.assert_called_once_with(
            "Trends request error: %s", "Connection timeout"
        )
        assert "Error fetching personalized trends" in str(exc_info.value)

    @patch("src.agentic_crypto_influencer.tools.trends_handler.requests.get")
    @patch("src.agentic_crypto_influencer.tools.trends_handler.logging.info")
    def test_get_personalized_trends_with_parameters(
        self, mock_logging_info: Mock, mock_requests_get: Mock
    ) -> None:
        """Test trends request with custom parameters"""
        access_token = "test_token"
        handler = TrendsHandler(access_token)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"trends": ["custom_trend"]}
        mock_requests_get.return_value = mock_response

        result = handler.get_personalized_trends("user123", max_results=5, exclude=["hashtags"])

        # Verify request was made
        mock_requests_get.assert_called_once()
        assert result == {"trends": ["custom_trend"]}


if __name__ == "__main__":
    unittest.main()
