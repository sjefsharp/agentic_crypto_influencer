"""
Tests for RedisHandler using pytest best practices.
"""

from unittest.mock import Mock, patch

import pytest

from tools.redis_handler import RedisHandler


@pytest.fixture
def redis_handler() -> RedisHandler:
    """RedisHandler instance with mocked redis client for testing."""
    handler = RedisHandler()
    handler.redis_client = Mock()  # type: ignore
    return handler


@pytest.mark.unit
def test_get(redis_handler: RedisHandler) -> None:
    """Test get method retrieves value from Redis."""
    redis_handler.redis_client.get.return_value = b"value"  # type: ignore
    result = redis_handler.get("key")
    assert result == b"value"


@pytest.mark.unit
def test_set(redis_handler: RedisHandler) -> None:
    """Test set method stores value in Redis."""
    redis_handler.set("key", "value")
    redis_handler.redis_client.set.assert_called_with("key", "value", ex=None)  # type: ignore


@pytest.mark.unit
def test_get_redis_error(redis_handler: RedisHandler) -> None:
    """Test get method with Redis error."""
    with patch("tools.redis_handler.logging.error") as mock_logging_error:
        redis_handler.redis_client.get.side_effect = Exception("Redis connection error")  # type: ignore

        with pytest.raises(RuntimeError) as exc_info:
            redis_handler.get("test_key")

        mock_logging_error.assert_called_once_with(
            "Failed to get key '%s' from Redis: %s",
            "test_key",
            "Redis connection error",
        )
        assert "Error retrieving key 'test_key' from Redis" in str(exc_info.value)


@pytest.mark.unit
def test_set_redis_error(redis_handler: RedisHandler) -> None:
    """Test set method with Redis error."""
    with patch("tools.redis_handler.logging.error") as mock_logging_error:
        redis_handler.redis_client.set.side_effect = Exception("Redis connection error")  # type: ignore

        with pytest.raises(RuntimeError) as exc_info:
            redis_handler.set("test_key", "test_value")

        mock_logging_error.assert_called_once_with(
            "Failed to set key '%s' in Redis: %s",
            "test_key",
            "Redis connection error",
        )
        assert "Error setting key 'test_key' in Redis" in str(exc_info.value)


@pytest.mark.unit
def test_set_with_expiry(redis_handler: RedisHandler) -> None:
    """Test set method with expiry parameter."""
    redis_handler.set("key", "value", ex=3600)
    redis_handler.redis_client.set.assert_called_with("key", "value", ex=3600)  # type: ignore


@pytest.mark.unit
def test_init_missing_redis_url() -> None:
    """Test initialization with missing REDIS_URL."""
    with patch("tools.redis_handler.REDIS_URL", ""):
        with pytest.raises(ValueError) as exc_info:
            RedisHandler()

        assert "REDIS_URL must be set in the environment variables" in str(
            exc_info.value
        )


@pytest.mark.unit
def test_init_redis_connection_success() -> None:
    """Test successful Redis connection during initialization."""
    with (
        patch("tools.redis_handler.REDIS_URL", "redis://localhost:6379"),
        patch("tools.redis_handler.logging.info") as mock_logging_info,
        patch("tools.redis_handler.Redis.from_url") as mock_redis_from_url,
    ):
        mock_redis_client = Mock()
        mock_redis_from_url.return_value = mock_redis_client

        handler = RedisHandler()

        mock_redis_from_url.assert_called_once_with("redis://localhost:6379")
        mock_logging_info.assert_called_once_with(
            "Connected to Redis at %s", "redis://localhost:6379"
        )
        assert handler.redis_client == mock_redis_client


@pytest.mark.unit
def test_init_redis_connection_failure() -> None:
    """Test Redis connection failure during initialization."""
    with (
        patch("tools.redis_handler.REDIS_URL", "redis://localhost:6379"),
        patch("tools.redis_handler.logging.error") as mock_logging_error,
        patch("tools.redis_handler.Redis.from_url") as mock_redis_from_url,
    ):
        mock_redis_from_url.side_effect = Exception("Connection failed")

        with pytest.raises(ConnectionError) as exc_info:
            RedisHandler()

        mock_logging_error.assert_called_once_with(
            "Failed to connect to Redis at %s: %s",
            "redis://localhost:6379",
            "Connection failed",
        )
        assert "Could not connect to Redis" in str(exc_info.value)
