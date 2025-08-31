import unittest
from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.oauth_handler import OAuthHandler


class TestOAuthHandler:
    def test_init(self) -> None:
        """Test OAuthHandler initialization"""
        with patch("src.agentic_crypto_influencer.tools.oauth_handler.RedisHandler") as mock_redis:
            mock_redis.return_value = Mock()
            handler = OAuthHandler()
            # Test that attributes are set
            assert handler.redis_handler is not None

    @patch("src.agentic_crypto_influencer.tools.oauth_handler.OAuth2Session")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.os.urandom")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.hashlib.sha256")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.base64.urlsafe_b64encode")
    def test_get_authorization_url(
        self, mock_b64encode: Mock, mock_sha256: Mock, mock_urandom: Mock, mock_oauth_session: Mock
    ) -> None:
        """Test getting authorization URL"""
        with patch("src.agentic_crypto_influencer.tools.oauth_handler.RedisHandler") as mock_redis:
            mock_redis.return_value = Mock()
            handler = OAuthHandler()

        # Mock random bytes
        mock_urandom.return_value = b"random_bytes_30_chars_long"

        # Mock base64 encoding - need to mock the decode() method
        mock_b64encode.return_value.decode.return_value = "code_challenge_with_special_chars!@#"

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

        url = handler.get_authorization_url()

        # Verify Redis calls
        handler.redis_handler.set.assert_any_call("code_verifier", "codechallengewithspecialchars")  # type: ignore[attr-defined]
        handler.redis_handler.set.assert_any_call("oauth_state", "state123")  # type: ignore[attr-defined]

        # Verify OAuth session creation
        mock_oauth_session.assert_called_once()

        # Verify authorization URL call
        mock_oauth.authorization_url.assert_called_once()

        # Verify return value
        assert url == "https://example.com/auth"

    @patch("src.agentic_crypto_influencer.tools.oauth_handler.OAuth2Session")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.json.dumps")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.logging.info")
    def test_exchange_code_for_tokens_success(
        self, mock_logging_info: Mock, mock_json_dumps: Mock, mock_oauth_session: Mock
    ) -> None:
        """Test successful token exchange"""
        handler = OAuthHandler()
        handler.redis_handler = Mock()

        # Mock Redis get
        handler.redis_handler.get.return_value = b"code_verifier_123"

        # Mock OAuth2Session
        mock_oauth = Mock()
        mock_token = {"access_token": "token123", "refresh_token": "refresh123"}
        mock_oauth.fetch_token.return_value = mock_token
        mock_oauth_session.return_value = mock_oauth

        # Mock json.dumps
        mock_json_dumps.return_value = '{"access_token": "token123"}'

        result = handler.exchange_code_for_tokens("auth_code_123")

        # Verify Redis calls
        handler.redis_handler.get.assert_called_once_with("code_verifier")
        handler.redis_handler.set.assert_called_once()

        # Verify OAuth session creation and token fetch
        mock_oauth_session.assert_called_once()
        mock_oauth.fetch_token.assert_called_once()

        # Verify logging - should be called twice: Redis connection + success message
        assert mock_logging_info.call_count == 2
        mock_logging_info.assert_any_call("Connected to Redis at %s", "redis://localhost:6379")
        mock_logging_info.assert_any_call("Tokens successfully saved to Redis.")

        # Verify return value
        assert result == mock_token

    def test_exchange_code_for_tokens_no_verifier(self) -> None:
        """Test token exchange without code verifier"""
        handler = OAuthHandler()
        handler.redis_handler = Mock()

        handler.redis_handler.get.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            handler.exchange_code_for_tokens("auth_code_123")

        assert "Code verifier not found in Redis" in str(exc_info.value)

    @patch("src.agentic_crypto_influencer.tools.oauth_handler.OAuth2Session")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.json.loads")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.json.dumps")
    @patch("src.agentic_crypto_influencer.tools.oauth_handler.logging.info")
    def test_refresh_access_token_success(
        self,
        mock_logging_info: Mock,
        mock_json_dumps: Mock,
        mock_json_loads: Mock,
        mock_oauth_session: Mock,
    ) -> None:
        """Test successful token refresh"""
        handler = OAuthHandler()
        handler.redis_handler = Mock()

        # Mock Redis get
        token_data = '{"access_token": "old_token", "refresh_token": "refresh123"}'
        handler.redis_handler.get.return_value = token_data.encode()

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

        result = handler.refresh_access_token()

        # Verify Redis calls
        handler.redis_handler.get.assert_called_once_with("token")
        handler.redis_handler.set.assert_called_once()

        # Verify OAuth session creation and token refresh
        mock_oauth_session.assert_called_once()
        mock_oauth.refresh_token.assert_called_once()

        # Verify logging - should be called twice: Redis connection + success message
        assert mock_logging_info.call_count == 2
        mock_logging_info.assert_any_call("Connected to Redis at %s", "redis://localhost:6379")
        mock_logging_info.assert_any_call(
            "Access token successfully refreshed and saved to Redis."
        )

        # Verify return value
        assert result == new_token

    def test_refresh_access_token_no_token(self) -> None:
        """Test token refresh without existing token"""
        handler = OAuthHandler()
        handler.redis_handler = Mock()

        handler.redis_handler.get.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            handler.refresh_access_token()

        assert "No token found in Redis" in str(exc_info.value)


if __name__ == "__main__":
    unittest.main()
