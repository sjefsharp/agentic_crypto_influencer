import json
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

        # Mock Redis to return valid token JSON
        mock_redis_instance = Mock()
        mock_redis_instance.get.return_value = '{"access_token": "test_token"}'
        mock_redis.return_value = mock_redis_instance

        mock_oauth.return_value.refresh_access_token.return_value = {"access_token": "test_token"}
        mock_trends.return_value = Mock()

        x = X()
        # The post method should now trigger lazy initialization and then fail validation
        with pytest.raises(ValueError, match="Post must be between 1 and 280 characters"):
            x.post("a" * 281)


class TestXComprehensive:
    def setup_method(self) -> None:
        """Set up test fixtures"""
        # Store patches for use in tests - initialization is now lazy
        self.redis_patch = patch("src.agentic_crypto_influencer.tools.x.RedisHandler")
        self.oauth_patch = patch("src.agentic_crypto_influencer.tools.x.OAuthHandler")
        self.post_patch = patch("src.agentic_crypto_influencer.tools.x.PostHandler")
        self.trends_patch = patch("src.agentic_crypto_influencer.tools.x.TrendsHandler")

        # Start the patches
        self.mock_redis_class = self.redis_patch.start()
        self.mock_oauth_class = self.oauth_patch.start()
        self.mock_post_class = self.post_patch.start()
        self.mock_trends_class = self.trends_patch.start()

        # Set up mock instances
        self.mock_redis = Mock()
        self.mock_redis.redis_client = Mock()
        # Mock redis get method to return proper JSON string for token
        self.mock_redis.get.return_value = (
            '{"access_token": "test_token", "refresh_token": "test_refresh"}'
        )
        self.mock_redis_class.return_value = self.mock_redis

        self.mock_oauth = Mock()
        self.mock_oauth.refresh_access_token.return_value = {"access_token": "test_token"}
        self.mock_oauth_class.return_value = self.mock_oauth

        self.mock_post = Mock()
        self.mock_post_class.return_value = self.mock_post

        self.mock_trends = Mock()
        self.mock_trends_class.return_value = self.mock_trends

        # Create X instance - no immediate token refresh
        self.x = X()

        # Explicitly set the mocked redis_handler to ensure our mocks are used
        self.x.redis_handler = self.mock_redis

    def teardown_method(self) -> None:
        """Clean up patches"""
        self.redis_patch.stop()
        self.oauth_patch.stop()
        self.post_patch.stop()
        self.trends_patch.stop()

    def test_init_success(self) -> None:
        """Test successful initialization - tokens are now initialized lazily"""
        # Verify initial state - no immediate token refresh
        assert self.x.redis_handler is not None
        assert self.x.access_token is None  # Lazy initialization
        assert self.x.post_handler is None  # Lazy initialization
        assert self.x.trends_handler is None  # Lazy initialization

        # Verify that calling post triggers lazy initialization
        self.mock_post.return_value.post_message.return_value = {"data": {"id": "123"}}
        self.x.post("Test message")

        # Verify token was initialized
        assert self.x.access_token == {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
        }
        assert self.x.post_handler is not None
        assert self.x.trends_handler is not None

    def test_init_missing_access_token(self) -> None:
        """Test initialization with missing access token - error occurs during lazy init"""
        # Create instance normally (no immediate token refresh)
        x = X()

        # Configure mock to return empty token data from Redis
        self.mock_redis.get.return_value = json.dumps({"access_token": ""})

        # Error should occur when trying to use post method (lazy initialization)
        with pytest.raises(RuntimeError) as exc_info:
            x.post("Test message")
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


# Additional tests to improve coverage
@patch("src.agentic_crypto_influencer.tools.x.get_logger")
@patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
@patch("src.agentic_crypto_influencer.tools.x.X")
def test_main_critical_error(
    mock_x_class: Mock, mock_error_manager_class: Mock, mock_get_logger: Mock
) -> None:
    """Test main function handles critical errors."""
    # Setup mocks
    mock_error_manager = Mock()
    mock_error_manager.handle_error.return_value = "Critical error handled"
    mock_error_manager_class.return_value = mock_error_manager

    mock_x = Mock()
    mock_x.post.side_effect = Exception("Critical system error")
    mock_x_class.return_value = mock_x

    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    # Import and run main
    from src.agentic_crypto_influencer.tools.x import main

    main()

    # Verify critical error handling
    mock_error_manager.handle_error.assert_called_once_with(mock_x.post.side_effect)
    mock_logger.critical.assert_any_call("Unexpected error: Critical error handled")


@patch("src.agentic_crypto_influencer.tools.x.X_USER_ID", "test_user_123")
@patch("src.agentic_crypto_influencer.tools.x.get_logger")
@patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
@patch("src.agentic_crypto_influencer.tools.x.X")
def test_main_with_user_id_trends_error(
    mock_x_class: Mock, mock_error_manager_class: Mock, mock_get_logger: Mock
) -> None:
    """Test main function when trends fetching fails but posting succeeds."""
    # Setup mocks
    mock_error_manager = Mock()
    mock_error_manager.handle_error.return_value = "Trends error handled"
    mock_error_manager_class.return_value = mock_error_manager

    mock_x = Mock()
    mock_x.post.return_value = {"id": "123", "text": "Post"}
    mock_x.get_personalized_trends.side_effect = Exception("Trends API failed")
    mock_x_class.return_value = mock_x

    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    # Import and run main
    from src.agentic_crypto_influencer.tools.x import main

    main()

    # Verify posting succeeded but trends failed
    mock_x.post.assert_called_once_with("Post")
    mock_x.get_personalized_trends.assert_called_once_with(user_id="test_user_123", max_results=10)
    mock_logger.error.assert_any_call("Failed to fetch personalized trends: Trends API failed")
    mock_error_manager.handle_error.assert_called_once_with(
        mock_x.get_personalized_trends.side_effect
    )


@patch("src.agentic_crypto_influencer.tools.x.X_USER_ID", "")
@patch("src.agentic_crypto_influencer.tools.x.get_logger")
@patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
@patch("src.agentic_crypto_influencer.tools.x.X")
def test_main_no_user_id(
    mock_x_class: Mock, mock_error_manager_class: Mock, mock_get_logger: Mock
) -> None:
    """Test main function when X_USER_ID is not set."""
    # Setup mocks
    mock_error_manager = Mock()
    mock_error_manager_class.return_value = mock_error_manager

    mock_x = Mock()
    mock_x.post.return_value = {"id": "123", "text": "Post"}
    mock_x_class.return_value = mock_x

    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    # Import and run main
    from src.agentic_crypto_influencer.tools.x import main

    main()

    # Verify posting succeeded but no trends fetch attempted
    mock_x.post.assert_called_once_with("Post")
    mock_x.get_personalized_trends.assert_not_called()
    mock_logger.info.assert_any_call("X_USER_ID not set; skipping personalized trends fetch")


@patch("src.agentic_crypto_influencer.tools.x.X_USER_ID", "test_user_123")
@patch("src.agentic_crypto_influencer.tools.x.get_logger")
@patch("src.agentic_crypto_influencer.tools.x.ErrorManager")
@patch("src.agentic_crypto_influencer.tools.x.X")
def test_main_successful_with_trends(
    mock_x_class: Mock, mock_error_manager_class: Mock, mock_get_logger: Mock
) -> None:
    """Test main function successful execution with trends."""
    # Setup mocks
    mock_error_manager = Mock()
    mock_error_manager_class.return_value = mock_error_manager

    mock_x = Mock()
    mock_x.post.return_value = {"id": "123", "text": "Post"}
    mock_x.get_personalized_trends.return_value = [{"name": "#Bitcoin", "volume": 12345}]
    mock_x_class.return_value = mock_x

    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    # Import and run main
    from src.agentic_crypto_influencer.tools.x import main

    main()

    # Verify successful execution
    mock_x.post.assert_called_once_with("Post")
    mock_x.get_personalized_trends.assert_called_once_with(user_id="test_user_123", max_results=10)
    mock_logger.info.assert_any_call(
        "Post Results", extra={"result": {"id": "123", "text": "Post"}}
    )
    mock_logger.info.assert_any_call(
        "Personalized Trends", extra={"trends": [{"name": "#Bitcoin", "volume": 12345}]}
    )
