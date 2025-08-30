from unittest.mock import MagicMock, Mock, patch

import pytest

from tools.x import X


def test_post_length():
    x = X()
    with pytest.raises(ValueError):
        x.post("a" * 281)


class TestXComprehensive:
    def setup_method(self):
        """Set up test fixtures"""
        # Mock all the dependencies
        with (
            patch("tools.x.RedisHandler") as mock_redis_class,
            patch("tools.x.OAuthHandler") as mock_oauth_class,
            patch("tools.x.PostHandler") as mock_post_class,
            patch("tools.x.TrendsHandler") as mock_trends_class,
        ):
            # Set up mock instances
            mock_redis = Mock()
            mock_redis.redis_client = Mock()
            mock_redis_class.return_value = mock_redis

            mock_oauth = Mock()
            mock_oauth.refresh_access_token.return_value = {
                "access_token": "test_token"
            }
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

    def test_init_success(self):
        """Test successful initialization"""
        with (
            patch("tools.x.RedisHandler") as mock_redis_class,
            patch("tools.x.OAuthHandler") as mock_oauth_class,
            patch("tools.x.PostHandler") as mock_post_class,
            patch("tools.x.TrendsHandler") as mock_trends_class,
        ):
            # Set up mock instances
            mock_redis = Mock()
            mock_redis.redis_client = Mock()
            mock_redis_class.return_value = mock_redis

            mock_oauth = Mock()
            mock_oauth.refresh_access_token.return_value = {
                "access_token": "test_token"
            }
            mock_oauth_class.return_value = mock_oauth

            mock_post = Mock()
            mock_post_class.return_value = mock_post

            mock_trends = Mock()
            mock_trends_class.return_value = mock_trends

            x = X()

            # Verify initialization
            assert x.redis_client == mock_redis.redis_client
            assert x.access_token == {"access_token": "test_token"}

    def test_init_missing_access_token(self):
        """Test initialization with missing access token"""
        with (
            patch("tools.x.RedisHandler") as mock_redis_class,
            patch("tools.x.OAuthHandler") as mock_oauth_class,
        ):
            mock_redis = Mock()
            mock_redis.redis_client = Mock()
            mock_redis_class.return_value = mock_redis

            mock_oauth = Mock()
            mock_oauth.refresh_access_token.return_value = {
                "access_token": ""
            }  # Empty token
            mock_oauth_class.return_value = mock_oauth

            with pytest.raises(RuntimeError) as exc_info:
                X()
            assert "Access token is missing or invalid" in str(exc_info.value)

    def test_post_success(self):
        """Test successful post"""
        expected_response = {"id": "123", "text": "Test post"}
        self.mock_post.post_message.return_value = expected_response

        result = self.x.post("Test message")

        assert result == expected_response
        self.mock_post.post_message.assert_called_once_with("Test message")

    def test_get_personalized_trends_success(self):
        """Test successful personalized trends fetch"""
        expected_trends = {"trends": ["#Bitcoin", "#Crypto"]}
        self.mock_trends.get_personalized_trends.return_value = expected_trends

        result = self.x.get_personalized_trends("user123", 10, ["hashtags"])

        assert result == expected_trends
        self.mock_trends.get_personalized_trends.assert_called_once_with(
            "user123", 10, ["hashtags"]
        )

    def test_get_personalized_trends_default_params(self):
        """Test personalized trends with default parameters"""
        expected_trends = {"trends": ["#Bitcoin"]}
        self.mock_trends.get_personalized_trends.return_value = expected_trends

        result = self.x.get_personalized_trends("user123")

        assert result == expected_trends
        self.mock_trends.get_personalized_trends.assert_called_once_with(
            "user123", 10, None
        )

    @patch("tools.x.ErrorManager")
    @patch("tools.x.X")
    def test_main_success(
        self, mock_x_class: MagicMock, mock_error_manager_class: MagicMock
    ):
        """Test main function success path"""
        # Mock the X instance and error manager
        mock_x = Mock()
        mock_x.post.return_value = {"id": "123", "text": "Test post"}
        mock_x.get_personalized_trends.return_value = {"trends": ["#Bitcoin"]}
        mock_x_class.return_value = mock_x

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager

        with (
            patch("tools.x.X_USER_ID", "test_user_id"),
            patch("builtins.print") as mock_print,
        ):
            # Import and run main
            from tools.x import main

            main()

        # Verify calls
        mock_print.assert_any_call("--- Post Results ---")
        mock_print.assert_any_call({"id": "123", "text": "Test post"})
        mock_print.assert_any_call("--- Personalized Trends ---")
        mock_print.assert_any_call({"trends": ["#Bitcoin"]})

    @patch("tools.x.ErrorManager")
    @patch("tools.x.X")
    def test_main_no_user_id(
        self, mock_x_class: MagicMock, mock_error_manager_class: MagicMock
    ):
        """Test main function without user ID"""
        # Mock the X instance and error manager
        mock_x = Mock()
        mock_x.post.return_value = {"id": "123", "text": "Test post"}
        mock_x_class.return_value = mock_x

        mock_error_manager = Mock()
        mock_error_manager_class.return_value = mock_error_manager

        with patch("tools.x.X_USER_ID", ""), patch("builtins.print") as mock_print:
            # Import and run main
            from tools.x import main

            main()

        # Verify calls
        mock_print.assert_any_call("--- Post Results ---")
        mock_print.assert_any_call({"id": "123", "text": "Test post"})

    @patch("tools.x.ErrorManager")
    @patch("tools.x.X")
    def test_main_post_error(
        self, mock_x_class: MagicMock, mock_error_manager_class: MagicMock
    ):
        """Test main function with post error"""
        # Mock the X instance to raise error
        mock_x = Mock()
        mock_x.post.side_effect = ValueError("Invalid post")
        mock_x_class.return_value = mock_x

        mock_error_manager = Mock()
        mock_error_manager.handle_error.return_value = "Handled error message"
        mock_error_manager_class.return_value = mock_error_manager

        with patch("tools.x.X_USER_ID", ""), patch("builtins.print") as mock_print:
            # Import and run main
            from tools.x import main

            main()

        # Verify error handling
        mock_error_manager.handle_error.assert_called_once_with(mock_x.post.side_effect)
        mock_print.assert_called_once_with("Handled error message")
