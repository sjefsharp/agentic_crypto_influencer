import unittest
from unittest.mock import Mock, patch

from tools.oauth_handler import OAuthHandler


class TestOAuthHandler(unittest.TestCase):
    def setUp(self):
        self.handler = OAuthHandler()
        self.handler.redis_handler = Mock()

    def test_init(self):
        """Test OAuthHandler initialization"""
        # Test that attributes are set (mocked in setUp)
        self.assertIsNotNone(self.handler.redis_handler)

    @patch("tools.oauth_handler.OAuth2Session")
    @patch("tools.oauth_handler.os.urandom")
    @patch("tools.oauth_handler.hashlib.sha256")
    @patch("tools.oauth_handler.base64.urlsafe_b64encode")
    def test_get_authorization_url(
        self, mock_b64encode, mock_sha256, mock_urandom, mock_oauth_session
    ):
        """Test getting authorization URL"""
        # Mock random bytes
        mock_urandom.return_value = b"random_bytes_30_chars_long"

        # Mock base64 encoding - need to mock the decode() method
        mock_b64encode.return_value.decode.return_value = (
            "code_challenge_with_special_chars!@#"
        )

        # Mock SHA256
        mock_hash = Mock()
        mock_hash.digest.return_value = b"hash_bytes"
        mock_sha256.return_value = mock_hash

        # Mock OAuth2Session
        mock_oauth = Mock()
        mock_oauth.authorization_url.return_value = (
            "https://example.com/auth",
            "state123",
        )
        mock_oauth_session.return_value = mock_oauth

        url = self.handler.get_authorization_url()

        # Verify Redis calls
        self.handler.redis_handler.set.assert_any_call(
            "code_verifier", "codechallengewithspecialchars"
        )
        self.handler.redis_handler.set.assert_any_call("oauth_state", "state123")

        # Verify OAuth session creation
        mock_oauth_session.assert_called_once()

        # Verify authorization URL call
        mock_oauth.authorization_url.assert_called_once()

        # Verify return value
        self.assertEqual(url, "https://example.com/auth")

    @patch("tools.oauth_handler.OAuth2Session")
    @patch("tools.oauth_handler.json.dumps")
    @patch("tools.oauth_handler.logging.info")
    def test_exchange_code_for_tokens_success(
        self, mock_logging_info, mock_json_dumps, mock_oauth_session
    ):
        """Test successful token exchange"""
        # Mock Redis get
        self.handler.redis_handler.get.return_value = b"code_verifier_123"

        # Mock OAuth2Session
        mock_oauth = Mock()
        mock_token = {"access_token": "token123", "refresh_token": "refresh123"}
        mock_oauth.fetch_token.return_value = mock_token
        mock_oauth_session.return_value = mock_oauth

        # Mock json.dumps
        mock_json_dumps.return_value = '{"access_token": "token123"}'

        result = self.handler.exchange_code_for_tokens("auth_code_123")

        # Verify Redis calls
        self.handler.redis_handler.get.assert_called_once_with("code_verifier")
        self.handler.redis_handler.set.assert_called_once()

        # Verify OAuth session creation and token fetch
        mock_oauth_session.assert_called_once()
        mock_oauth.fetch_token.assert_called_once()

        # Verify logging
        mock_logging_info.assert_called_once_with("Tokens successfully saved to Redis.")

        # Verify return value
        self.assertEqual(result, mock_token)

    def test_exchange_code_for_tokens_no_verifier(self):
        """Test token exchange without code verifier"""
        self.handler.redis_handler.get.return_value = None

        with self.assertRaises(RuntimeError) as context:
            self.handler.exchange_code_for_tokens("auth_code_123")

        self.assertIn("Code verifier not found in Redis", str(context.exception))

    @patch("tools.oauth_handler.OAuth2Session")
    @patch("tools.oauth_handler.json.loads")
    @patch("tools.oauth_handler.json.dumps")
    @patch("tools.oauth_handler.logging.info")
    def test_refresh_access_token_success(
        self, mock_logging_info, mock_json_dumps, mock_json_loads, mock_oauth_session
    ):
        """Test successful token refresh"""
        # Mock Redis get
        token_data = '{"access_token": "old_token", "refresh_token": "refresh123"}'
        self.handler.redis_handler.get.return_value = token_data.encode()

        # Mock json.loads
        mock_json_loads.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh123",
        }

        # Mock OAuth2Session
        mock_oauth = Mock()
        new_token = {"access_token": "new_token", "refresh_token": "refresh123"}
        mock_oauth.refresh_token.return_value = new_token
        mock_oauth_session.return_value = mock_oauth

        # Mock json.dumps
        mock_json_dumps.return_value = '{"access_token": "new_token"}'

        result = self.handler.refresh_access_token()

        # Verify Redis calls
        self.handler.redis_handler.get.assert_called_once_with("token")
        self.handler.redis_handler.set.assert_called_once()

        # Verify OAuth session creation and token refresh
        mock_oauth_session.assert_called_once()
        mock_oauth.refresh_token.assert_called_once()

        # Verify logging
        mock_logging_info.assert_called_once_with(
            "Access token successfully refreshed and saved to Redis."
        )

        # Verify return value
        self.assertEqual(result, new_token)

    def test_refresh_access_token_no_token(self):
        """Test token refresh without existing token"""
        self.handler.redis_handler.get.return_value = None

        with self.assertRaises(RuntimeError) as context:
            self.handler.refresh_access_token()

        self.assertIn("No token found in Redis", str(context.exception))


if __name__ == "__main__":
    unittest.main()
