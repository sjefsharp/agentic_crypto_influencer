import unittest
from unittest.mock import Mock, patch

from tools.trends_handler import TrendsHandler


class TestTrendsHandler(unittest.TestCase):
    def setUp(self):
        self.access_token = "test_token"
        self.handler = TrendsHandler(self.access_token)

    def test_init(self):
        """Test TrendsHandler initialization"""
        self.assertEqual(self.handler.access_token, self.access_token)

    @patch("tools.trends_handler.requests.get")
    @patch("tools.trends_handler.logging.info")
    def test_get_personalized_trends_success(
        self, mock_logging_info: Mock, mock_requests_get: Mock
    ):
        """Test successful trends retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"trends": ["trend1", "trend2"]}
        mock_requests_get.return_value = mock_response

        result = self.handler.get_personalized_trends("user123")

        # Verify request was made correctly
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        self.assertIn("Bearer test_token", call_args[1]["headers"]["Authorization"])
        self.assertEqual(call_args[1]["timeout"], 15)

        # Verify logging
        mock_logging_info.assert_called_once_with("Trends response status: %d", 200)

        # Verify return value
        self.assertEqual(result, {"trends": ["trend1", "trend2"]})

    @patch("tools.trends_handler.requests.get")
    @patch("tools.trends_handler.logging.error")
    def test_get_personalized_trends_request_error(
        self, mock_logging_error: Mock, mock_requests_get: Mock
    ):
        """Test trends request with error response"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.handler.get_personalized_trends("user123")

        mock_logging_error.assert_any_call(
            "Trends request failed: %d %s", 401, "Unauthorized"
        )
        mock_logging_error.assert_any_call(
            "Trends request error: %s",
            "Trends request returned an error: 401 Unauthorized",
        )
        self.assertIn("Trends request returned an error: 401", str(context.exception))

    @patch("tools.trends_handler.requests.get")
    @patch("tools.trends_handler.logging.error")
    def test_get_personalized_trends_network_error(
        self, mock_logging_error: Mock, mock_requests_get: Mock
    ):
        """Test trends request with network error"""
        mock_requests_get.side_effect = Exception("Connection timeout")

        with self.assertRaises(RuntimeError) as context:
            self.handler.get_personalized_trends("user123")

        mock_logging_error.assert_called_once_with(
            "Trends request error: %s", "Connection timeout"
        )
        self.assertIn("Error fetching personalized trends", str(context.exception))

    @patch("tools.trends_handler.requests.get")
    @patch("tools.trends_handler.logging.info")
    def test_get_personalized_trends_with_parameters(
        self, mock_logging_info: Mock, mock_requests_get: Mock
    ):
        """Test trends request with custom parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"trends": ["custom_trend"]}
        mock_requests_get.return_value = mock_response

        result = self.handler.get_personalized_trends(
            "user123", max_results=5, exclude=["hashtags"]
        )

        # Verify request was made
        mock_requests_get.assert_called_once()
        self.assertEqual(result, {"trends": ["custom_trend"]})


if __name__ == "__main__":
    unittest.main()
