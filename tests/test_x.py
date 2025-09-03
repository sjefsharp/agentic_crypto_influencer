from unittest.mock import MagicMock, Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.x import X


def test_post_length() -> None:
    """Test that X.post validates post length by delegating to PostHandler."""
    with (
        patch("src.agentic_crypto_influencer.tools.x.RedisHandler") as mock_redis,
        patch("src.agentic_crypto_influencer.tools.x.OAuthHandler") as mock_oauth,
        patch("src.agentic_crypto_influencer.tools.x.PostHandler") as mock_post,
        patch("src.agentic_crypto_influencer.tools.x.TrendsHandler") as mock_trends,
    ):
        # Mock the PostHandler to raise ValueError for invalid length
        mock_post_instance = Mock()
        mock_post_instance.post_message.side_effect = ValueError(
            "Post must be between 1 and 280 characters"
        )
        mock_post.return_value = mock_post_instance

        mock_redis.return_value.redis_client = Mock()
        mock_oauth.return_value.refresh_access_token.return_value = {"access_token": "test_token"}
        mock_trends.return_value = Mock()

        x = X()
        with pytest.raises(ValueError, match="Post must be between 1 and 280 characters"):
            x.post("a" * 281)


class TestXComprehensive:
    def setup_method(self) -> None:
        """Set up test fixtures"""
        # Mock all the dependencies
        with (
            patch("src.agentic_crypto_influencer.tools.x.RedisHandler") as mock_redis_class,
            patch("src.agentic_crypto_influencer.tools.x.OAuthHandler") as mock_oauth_class,
            patch("src.agentic_crypto_influencer.tools.x.PostHandler") as mock_post_class,
            patch("src.agentic_crypto_influencer.tools.x.TrendsHandler") as mock_trends_class,
        ):
            # Set up mock instances
            mock_redis = Mock()
            mock_redis.redis_client = Mock()
            mock_redis_class.return_value = mock_redis

            mock_oauth = Mock()
            mock_oauth.refresh_access_token.return_value = {"access_token": "test_token"}
            mock_oauth_class.return_value = mock_oauth

            mock_post = Mock()
            mock_post_class.return_value = mock_post

            mock_trends = Mock()
            mock_trends_class.return_value = mock_trends

            self.x = X()

            # Store mocks for use in tests
            self.mock_redis = mock_redis
            self.mock_oauth = mock_oauth
            self.mock_post = mock_post
            self.mock_trends = mock_trends

    def test_init_success(self) -> None:
        """Test successful initialization"""
        with (
            patch("src.agentic_crypto_influencer.tools.x.RedisHandler") as mock_redis_class,
            patch("src.agentic_crypto_influencer.tools.x.OAuthHandler") as mock_oauth_class,
            patch("src.agentic_crypto_influencer.tools.x.PostHandler") as mock_post_class,
            patch("src.agentic_crypto_influencer.tools.x.TrendsHandler") as mock_trends_class,
        ):
            # Set up mock instances
            mock_redis = Mock()
            mock_redis.redis_client = Mock()
            mock_redis_class.return_value = mock_redis

            mock_oauth = Mock()
            mock_oauth.refresh_access_token.return_value = {"access_token": "test_token"}
            mock_oauth_class.return_value = mock_oauth

            mock_post = Mock()
            mock_post_class.return_value = mock_post

            mock_trends = Mock()
            mock_trends_class.return_value = mock_trends

            x = X()

            # Verify initialization
            assert x.redis_client == mock_redis.redis_client
            assert x.access_token == {"access_token": "test_token"}

    def test_init_missing_access_token(self) -> None:
        """Test initialization with missing access token"""
        with (
            patch("src.agentic_crypto_influencer.tools.x.RedisHandler") as mock_redis_class,
            patch("src.agentic_crypto_influencer.tools.x.OAuthHandler") as mock_oauth_class,
        ):
            mock_redis = Mock()
            mock_redis.redis_client = Mock()
            mock_redis_class.return_value = mock_redis

            mock_oauth = Mock()
            mock_oauth.refresh_access_token.return_value = {"access_token": ""}  # Empty token
            mock_oauth_class.return_value = mock_oauth

            with pytest.raises(RuntimeError) as exc_info:
                X()
            assert "Access token is missing or invalid" in str(exc_info.value)

    def test_post_success(self) -> None:
        """Test successful post"""
        expected_response = {"id": "123", "text": "Test post"}
        self.mock_post.post_message.return_value = expected_response

        result = self.x.post("Test message")

        assert result == expected_response
        self.mock_post.post_message.assert_called_once_with("Test message")

    def test_get_personalized_trends_success(self) -> None:
        """Test successful personalized trends fetch"""
        expected_trends = {"trends": ["#Bitcoin", "#Crypto"]}
        self.mock_trends.get_personalized_trends.return_value = expected_trends

        result = self.x.get_personalized_trends("user123", 10, ["hashtags"])

        assert result == expected_trends
        self.mock_trends.get_personalized_trends.assert_called_once_with(
            "user123", 10, ["hashtags"]
        )

    def test_get_personalized_trends_default_params(self) -> None:
        """Test personalized trends with default parameters"""
        expected_trends = {"trends": ["#Bitcoin"]}
        self.mock_trends.get_personalized_trends.return_value = expected_trends

        result = self.x.get_personalized_trends("user123")

        assert result == expected_trends
        self.mock_trends.get_personalized_trends.assert_called_once_with("user123", 10, None)

    @patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.x.X")
    def test_main_success(
        self, mock_x_class: MagicMock, mock_error_manager_class: MagicMock
    ) -> None:
        """Test main function success path"""
        # Mock the X instance and error manager
        mock_x = Mock()
        mock_x.post.return_value = {"id": "123", "text": "Test post"}
        mock_x.get_personalized_trends.return_value = {"trends": ["#Bitcoin"]}
        mock_x_class.return_value = mock_x

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager

        with (
            patch("src.agentic_crypto_influencer.tools.x.X_USER_ID", "test_user_id"),
            patch("src.agentic_crypto_influencer.tools.x.get_logger") as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Import and run main
            from src.agentic_crypto_influencer.tools.x import main

            main()

        # Verify logger calls
        mock_logger.info.assert_any_call("Starting X posting workflow")
        mock_logger.info.assert_any_call(
            "Post Results", extra={"result": {"id": "123", "text": "Test post"}}
        )
        mock_logger.info.assert_any_call(
            "Personalized Trends", extra={"trends": {"trends": ["#Bitcoin"]}}
        )

    @patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.x.X")
    def test_main_no_user_id(
        self, mock_x_class: MagicMock, mock_error_manager_class: MagicMock
    ) -> None:
        """Test main function without user ID"""
        # Mock the X instance and error manager
        mock_x = Mock()
        mock_x.post.return_value = {"id": "123", "text": "Test post"}
        mock_x_class.return_value = mock_x

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager

        with (
            patch("src.agentic_crypto_influencer.tools.x.X_USER_ID", None),
            patch("src.agentic_crypto_influencer.tools.x.get_logger") as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Import and run main
            from src.agentic_crypto_influencer.tools.x import main

            main()

        # Verify logger calls - should post but not get trends
        mock_logger.info.assert_any_call("Starting X posting workflow")
        mock_logger.info.assert_any_call(
            "Post Results", extra={"result": {"id": "123", "text": "Test post"}}
        )
        mock_logger.info.assert_any_call("X_USER_ID not set; skipping personalized trends fetch")

    @patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
    @patch("src.agentic_crypto_influencer.tools.x.X")
    def test_main_post_error(
        self, mock_x_class: MagicMock, mock_error_manager_class: MagicMock
    ) -> None:
        """Test main function with post error"""
        # Mock the X instance to raise error
        mock_x = Mock()
        mock_x.post.side_effect = ValueError("Invalid post")
        mock_x_class.return_value = mock_x

        mock_error_manager = Mock()
        mock_error_manager.handle_error.return_value = "Handled error message"
        mock_error_manager_class.return_value = mock_error_manager

        with (
            patch("src.agentic_crypto_influencer.tools.x.X_USER_ID", ""),
            patch("src.agentic_crypto_influencer.tools.x.get_logger") as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Import and run main
            from src.agentic_crypto_influencer.tools.x import main

            main()

        # Verify error handling and logging
        mock_error_manager.handle_error.assert_called_once_with(mock_x.post.side_effect)
        mock_logger.error.assert_any_call("Workflow error: Handled error message")
