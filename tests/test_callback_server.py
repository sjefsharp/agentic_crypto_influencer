# mypy: disable-error-code="misc"

import json
from typing import override
import unittest
from unittest.mock import Mock, patch

from src.agentic_crypto_influencer.tools.callback_server import app, get_and_save_tokens


class TestCallbackServer(unittest.TestCase):
    @override
    def setUp(self) -> None:
        """Set up test fixtures"""
        self.app = app.test_client()
        # Note: Flask testing attribute is set during app creation

    @patch(
        "src.agentic_crypto_influencer.tools.callback_server.X_REDIRECT_URI",
        "http://localhost:5000/callback",
    )
    @patch(
        "src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_SECRET", "test_client_secret"
    )
    @patch("src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_ID", "test_client_id")
    @patch("src.agentic_crypto_influencer.tools.callback_server.requests.post")
    @patch("src.agentic_crypto_influencer.tools.callback_server.RedisHandler")
    @patch("src.agentic_crypto_influencer.tools.callback_server.logger")
    def test_get_and_save_tokens_success(
        self, mock_logger: Mock, mock_redis_handler_class: Mock, mock_requests_post: Mock
    ) -> None:
        """Test successful token retrieval and saving"""
        # Mock the Redis handler
        mock_redis_handler = Mock()
        mock_redis_handler_class.return_value = mock_redis_handler

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
        mock_requests_post.return_value = mock_response

        # Test the function
        result = get_and_save_tokens("test_code")

        # Verify the result
        assert result

        # Verify HTTP request was made correctly
        # The mock should be called at least once for the token request
        assert mock_requests_post.call_count >= 1
        call_args = mock_requests_post.call_args_list[0]  # Get the first call
        assert call_args[0][0] == "https://api.x.com/2/oauth2/token"
        assert "code" in call_args[1]["data"]
        assert call_args[1]["data"]["code"] == "test_code"

        # Verify Redis storage
        mock_redis_handler.set.assert_called_once()
        stored_data = json.loads(mock_redis_handler.set.call_args[0][1])
        assert stored_data["access_token"] == "test_access_token"
        assert stored_data["refresh_token"] == "test_refresh_token"

        # Verify logging
        assert mock_logger.info.call_count >= 2  # At least 2 info calls

    @patch("src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_ID", None)
    def test_get_and_save_tokens_missing_config(self) -> None:
        """Test token retrieval with missing configuration"""
        # Function should return False and not raise exception
        result = get_and_save_tokens("test_code")
        assert result is False

    def test_get_and_save_tokens_no_code(self) -> None:
        """Test token retrieval with no authorization code"""
        # Function should return False and not raise exception
        result = get_and_save_tokens("")
        assert result is False

    @patch(
        "src.agentic_crypto_influencer.tools.callback_server.X_REDIRECT_URI",
        "http://localhost:5000/callback",
    )
    @patch(
        "src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_SECRET", "test_client_secret"
    )
    @patch("src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_ID", "test_client_id")
    @patch("src.agentic_crypto_influencer.tools.callback_server.requests.post")
    @patch("src.agentic_crypto_influencer.tools.callback_server.logger")
    def test_get_and_save_tokens_http_error(
        self, mock_logger: Mock, mock_requests_post: Mock
    ) -> None:
        """Test token retrieval with HTTP error"""
        # Mock HTTP request to raise exception
        import requests

        mock_requests_post.side_effect = requests.exceptions.RequestException("HTTP Error")

        # Test the function - it should return False on error
        result = get_and_save_tokens("test_code")

        # Verify the result
        assert not result

        # Verify error logging was called at least once
        assert mock_logger.error.call_count >= 1

    def test_health_route(self) -> None:
        """Test the health check route"""
        response = self.app.get("/health")
        assert response.status_code == 200
        assert "OAuth Callback Service is healthy" in response.get_data(as_text=True)

    def test_home_route(self) -> None:
        """Test the home route with valid configuration"""
        with (
            patch("src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_ID", "test_id"),
            patch(
                "src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_SECRET",
                "test_secret",
            ),
            patch(
                "src.agentic_crypto_influencer.tools.callback_server.X_REDIRECT_URI",
                "http://localhost:5000/callback",
            ),
            patch(
                "src.agentic_crypto_influencer.tools.oauth_handler.get_authorization_url",
                return_value="https://twitter.com/i/oauth2/authorize?test=params",
            ),
        ):
            response = self.app.get("/")
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            assert "X/Twitter OAuth2Session Callback Service" in response_text
            assert "Authorize with X/Twitter" in response_text

    def test_home_route_missing_config(self) -> None:
        """Test the home route with missing configuration"""
        with patch("src.agentic_crypto_influencer.tools.callback_server.X_CLIENT_ID", None):
            response = self.app.get("/")
            assert response.status_code == 500
            response_text = response.get_data(as_text=True)
            assert "OAuth configuration missing" in response_text

    @patch("src.agentic_crypto_influencer.tools.callback_server.get_and_save_tokens")
    def test_callback_route_success(self, mock_get_and_save_tokens: Mock) -> None:
        """Test successful callback processing"""
        # Test the route
        response = self.app.get("/callback?code=test_code")
        assert response.status_code == 200
        assert "Autorisatie succesvol" in response.get_data(as_text=True)

        # Verify get_and_save_tokens was called
        mock_get_and_save_tokens.assert_called_once_with("test_code")

    def test_callback_route_no_code(self) -> None:
        """Test callback route with no authorization code"""
        response = self.app.get("/callback")
        assert response.status_code == 400
        assert "Geen autorisatiecode gevonden" in response.get_data(as_text=True)

    @patch("src.agentic_crypto_influencer.tools.callback_server.RedisHandler")
    def test_test_authorization_route_success(self, mock_redis_handler_class: Mock) -> None:
        """Test successful authorization check"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = json.dumps(
            {"access_token": "test_access_token", "refresh_token": "test_refresh_token"}
        )
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        # Tokens are masked for security: test_access_token becomes test...oken
        assert "test...oken" in response_text
        assert "Tokens gevonden in Redis" in response_text

    @patch("src.agentic_crypto_influencer.tools.callback_server.RedisHandler")
    def test_test_authorization_route_no_tokens(self, mock_redis_handler_class: Mock) -> None:
        """Test authorization check with no tokens"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = None
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        assert response.status_code == 404
        assert "Geen tokens gevonden" in response.get_data(as_text=True)

    @patch("src.agentic_crypto_influencer.tools.callback_server.RedisHandler")
    def test_test_authorization_route_invalid_json(self, mock_redis_handler_class: Mock) -> None:
        """Test authorization check with invalid JSON"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = "invalid json"
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        assert response.status_code == 500
        assert "Fout bij het decoderen" in response.get_data(as_text=True)

    @patch("src.agentic_crypto_influencer.tools.callback_server.RedisHandler")
    def test_test_authorization_route_incomplete_tokens(
        self, mock_redis_handler_class: Mock
    ) -> None:
        """Test authorization check with incomplete tokens"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = json.dumps(
            {"access_token": "test_access_token"}  # Missing refresh_token
        )
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        assert response.status_code == 400
        assert "onvolledig" in response.get_data(as_text=True)


if __name__ == "__main__":
    unittest.main()
