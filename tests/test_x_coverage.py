"""
Additional tests for X (Twitter) API client to improve coverage.
"""

from unittest.mock import Mock, patch

import pytest

from tools.x import X


@pytest.mark.unit
def test_init_missing_redis_handler():
    """Test X initialization when RedisHandler is not available."""
    with patch("tools.x.RedisHandler", None):
        with pytest.raises(ImportError) as exc_info:
            X()
        assert "RedisHandler is not available" in str(exc_info.value)


@pytest.mark.unit
def test_init_missing_oauth_handler():
    """Test X initialization when OAuthHandler is not available."""
    with (
        patch("tools.x.RedisHandler") as mock_redis_class,
        patch("tools.x.OAuthHandler", None),
    ):
        mock_redis = Mock()
        mock_redis.redis_client = Mock()
        mock_redis_class.return_value = mock_redis

        with pytest.raises(ImportError) as exc_info:
            X()
        assert "OAuthHandler is not available" in str(exc_info.value)


@pytest.mark.unit
def test_init_missing_post_handler():
    """Test X initialization when PostHandler is not available."""
    with (
        patch("tools.x.RedisHandler") as mock_redis_class,
        patch("tools.x.OAuthHandler") as mock_oauth_class,
        patch("tools.x.PostHandler", None),
    ):
        mock_redis = Mock()
        mock_redis.redis_client = Mock()
        mock_redis_class.return_value = mock_redis

        mock_oauth = Mock()
        mock_oauth.refresh_access_token.return_value = {"access_token": "test_token"}
        mock_oauth_class.return_value = mock_oauth

        with pytest.raises(ImportError) as exc_info:
            X()
        assert "PostHandler is not available" in str(exc_info.value)


@pytest.mark.unit
def test_init_missing_trends_handler():
    """Test X initialization when TrendsHandler is not available."""
    with (
        patch("tools.x.RedisHandler") as mock_redis_class,
        patch("tools.x.OAuthHandler") as mock_oauth_class,
        patch("tools.x.PostHandler") as mock_post_class,
        patch("tools.x.TrendsHandler", None),
    ):
        mock_redis = Mock()
        mock_redis.redis_client = Mock()
        mock_redis_class.return_value = mock_redis

        mock_oauth = Mock()
        mock_oauth.refresh_access_token.return_value = {"access_token": "test_token"}
        mock_oauth_class.return_value = mock_oauth

        mock_post = Mock()
        mock_post_class.return_value = mock_post

        with pytest.raises(ImportError) as exc_info:
            X()
        assert "TrendsHandler is not available" in str(exc_info.value)


@pytest.mark.unit
def test_init_invalid_access_token():
    """Test X initialization with invalid access token."""
    with (
        patch("tools.x.RedisHandler") as mock_redis_class,
        patch("tools.x.OAuthHandler") as mock_oauth_class,
    ):
        mock_redis = Mock()
        mock_redis.redis_client = Mock()
        mock_redis_class.return_value = mock_redis

        mock_oauth = Mock()
        mock_oauth.refresh_access_token.return_value = {}  # No access_token key
        mock_oauth_class.return_value = mock_oauth

        with pytest.raises(RuntimeError) as exc_info:
            X()
        assert "Access token is missing or invalid" in str(exc_info.value)


@pytest.mark.unit
def test_get_personalized_trends_error():
    """Test personalized trends with error."""
    with (
        patch("tools.x.RedisHandler") as mock_redis_class,
        patch("tools.x.OAuthHandler") as mock_oauth_class,
        patch("tools.x.PostHandler") as mock_post_class,
        patch("tools.x.TrendsHandler") as mock_trends_class,
    ):
        mock_redis = Mock()
        mock_redis.redis_client = Mock()
        mock_redis_class.return_value = mock_redis

        mock_oauth = Mock()
        mock_oauth.refresh_access_token.return_value = {"access_token": "test_token"}
        mock_oauth_class.return_value = mock_oauth

        mock_post = Mock()
        mock_post_class.return_value = mock_post

        mock_trends = Mock()
        mock_trends.get_personalized_trends.side_effect = RuntimeError("API Error")
        mock_trends_class.return_value = mock_trends

        x = X()

        with pytest.raises(RuntimeError) as exc_info:
            x.get_personalized_trends("user123")

        assert "API Error" in str(exc_info.value)


@pytest.mark.unit
def test_main_trends_error():
    """Test main function with trends fetch error."""
    # Mock the X instance
    mock_x = Mock()
    mock_x.post.return_value = {"id": "123", "text": "Test post"}
    mock_x.get_personalized_trends.side_effect = Exception("Trends API Error")

    mock_error_manager = Mock()
    mock_error_manager.handle_error.return_value = "Handled trends error"

    with (
        patch("tools.x.X", return_value=mock_x),
        patch("tools.x.ErrorManager", return_value=mock_error_manager),
        patch("tools.x.X_USER_ID", "test_user_id"),
        patch("builtins.print") as mock_print,
        patch("tools.x.logging"),
    ):
        from tools.x import main

        main()

    # Verify error handling for trends
    mock_error_manager.handle_error.assert_called_once_with(
        mock_x.get_personalized_trends.side_effect
    )
    mock_print.assert_any_call("Handled trends error")


@pytest.mark.unit
def test_main_initialization_error():
    """Test main function with X initialization error."""
    mock_error_manager = Mock()
    mock_error_manager.handle_error.return_value = "Handled init error"

    with (
        patch("tools.x.X", side_effect=ImportError("Missing dependency")),
        patch("tools.x.ErrorManager", return_value=mock_error_manager),
        patch("tools.x.X_USER_ID", ""),
        patch("builtins.print") as mock_print,
    ):
        from tools.x import main

        main()

    # Verify error handling
    mock_error_manager.handle_error.assert_called_once()
    mock_print.assert_called_once_with("Handled init error")
