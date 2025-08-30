import json
import unittest
from unittest.mock import Mock, patch

from tools.callback_server import app, get_and_save_tokens


class TestCallbackServer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        # Note: Flask testing attribute is set during app creation

    @patch("tools.callback_server.X_REDIRECT_URI", "http://localhost:5000/callback")
    @patch("tools.callback_server.X_CLIENT_SECRET", "test_client_secret")
    @patch("tools.callback_server.X_CLIENT_ID", "test_client_id")
    @patch("tools.callback_server.requests.post")
    @patch("tools.callback_server.RedisHandler")
    @patch("tools.callback_server.logging.info")
    def test_get_and_save_tokens_success(
        self, mock_logging, mock_redis_handler_class, mock_requests_post
    ):
        """Test successful token retrieval and saving"""
        # Mock the Redis handler
        mock_redis_handler = Mock()
        mock_redis_handler_class.return_value = mock_redis_handler

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
        mock_requests_post.return_value = mock_response

        # Test the function
        result = get_and_save_tokens("test_code")

        # Verify the result
        self.assertTrue(result)

        # Verify HTTP request was made correctly
        # The mock should be called at least once for the token request
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        call_args = mock_requests_post.call_args_list[0]  # Get the first call
        self.assertEqual(call_args[0][0], "https://api.twitter.com/2/oauth2/token")
        self.assertIn("code", call_args[1]["data"])
        self.assertEqual(call_args[1]["data"]["code"], "test_code")

        # Verify Redis storage
        mock_redis_handler.set.assert_called_once()
        stored_data = json.loads(mock_redis_handler.set.call_args[0][1])
        self.assertEqual(stored_data["access_token"], "test_access_token")
        self.assertEqual(stored_data["refresh_token"], "test_refresh_token")

        # Verify logging
        self.assertEqual(mock_logging.call_count, 2)

    @patch("tools.callback_server.X_CLIENT_ID", None)
    def test_get_and_save_tokens_missing_config(self):
        """Test token retrieval with missing configuration"""
        with self.assertRaises(ValueError) as context:
            get_and_save_tokens("test_code")
        self.assertIn(
            "Niet alle vereiste omgevingsvariabelen zijn ingesteld",
            str(context.exception),
        )

    def test_get_and_save_tokens_no_code(self):
        """Test token retrieval with no authorization code"""
        with self.assertRaises(ValueError) as context:
            get_and_save_tokens("")
        self.assertIn("Geen autorisatiecode ontvangen", str(context.exception))

    @patch("tools.callback_server.X_REDIRECT_URI", "http://localhost:5000/callback")
    @patch("tools.callback_server.X_CLIENT_SECRET", "test_client_secret")
    @patch("tools.callback_server.X_CLIENT_ID", "test_client_id")
    @patch("tools.callback_server.requests.post")
    @patch("tools.callback_server.errormanager")
    def test_get_and_save_tokens_http_error(
        self, mock_errormanager, mock_requests_post
    ):
        """Test token retrieval with HTTP error"""
        # Mock HTTP request to raise exception
        import requests

        mock_requests_post.side_effect = requests.exceptions.RequestException(
            "HTTP Error"
        )

        # Test the function - it should return False on error
        result = get_and_save_tokens("test_code")

        # Verify the result
        self.assertFalse(result)

        # Verify error handling was called
        mock_errormanager.handle_error.assert_called_once()

    def test_shutdown_route(self):
        """Test the shutdown route"""
        with self.app.application.test_request_context():
            # Mock the terminate function in the request environ
            with patch("tools.callback_server.request") as mock_request:
                # Create a mock terminate function that doesn't return a coroutine
                mock_terminate = Mock()
                mock_terminate.return_value = None
                mock_request.environ = {"flask._terminate_server": mock_terminate}

                response = self.app.post("/shutdown")
                self.assertEqual(response.status_code, 200)
                self.assertIn("Server shutting down", response.get_data(as_text=True))

                # Verify terminate function was called
                mock_terminate.assert_called_once()

    def test_shutdown_route_no_terminate(self):
        """Test shutdown route when terminate function is not available"""
        with self.app.application.test_request_context():
            with patch("tools.callback_server.request") as mock_request:
                mock_request.environ.get.return_value = None

                response = self.app.post("/shutdown")
                self.assertEqual(response.status_code, 500)
                # The error message might be in the response data or in the error logs
                response_text = response.get_data(as_text=True)
                self.assertTrue(
                    "Internal Server Error" in response_text
                    or "RuntimeError" in response_text
                )

    @patch("tools.callback_server.Thread")
    @patch("tools.callback_server.get_and_save_tokens")
    def test_callback_route_success(self, mock_get_and_save_tokens, mock_thread_class):
        """Test successful callback processing"""
        # Mock the thread
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        # Test the route
        response = self.app.get("/callback?code=test_code")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Autorisatie succesvol", response.get_data(as_text=True))

        # Verify thread was started
        mock_thread_class.assert_called_once_with(
            target=mock_get_and_save_tokens, args=("test_code",)
        )
        mock_thread.start.assert_called_once()

    def test_callback_route_no_code(self):
        """Test callback route with no authorization code"""
        response = self.app.get("/callback")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Geen autorisatiecode gevonden", response.get_data(as_text=True))

    @patch("tools.callback_server.RedisHandler")
    def test_test_authorization_route_success(self, mock_redis_handler_class):
        """Test successful authorization check"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = json.dumps(
            {"access_token": "test_access_token", "refresh_token": "test_refresh_token"}
        )
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)
        self.assertIn("test_access_token", response_text)
        self.assertIn("test_refresh_token", response_text)

    @patch("tools.callback_server.RedisHandler")
    def test_test_authorization_route_no_tokens(self, mock_redis_handler_class):
        """Test authorization check with no tokens"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = None
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Geen tokens gevonden", response.get_data(as_text=True))

    @patch("tools.callback_server.RedisHandler")
    def test_test_authorization_route_invalid_json(self, mock_redis_handler_class):
        """Test authorization check with invalid JSON"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = "invalid json"
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        self.assertEqual(response.status_code, 500)
        self.assertIn("Fout bij het decoderen", response.get_data(as_text=True))

    @patch("tools.callback_server.RedisHandler")
    def test_test_authorization_route_incomplete_tokens(self, mock_redis_handler_class):
        """Test authorization check with incomplete tokens"""
        # Create a mock instance with explicit get method
        mock_instance = Mock()
        mock_instance.get.return_value = json.dumps(
            {"access_token": "test_access_token"}  # Missing refresh_token
        )
        mock_redis_handler_class.return_value = mock_instance

        # Test the route
        response = self.app.get("/test_authorization")
        self.assertEqual(response.status_code, 400)
        self.assertIn("onvolledig", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
