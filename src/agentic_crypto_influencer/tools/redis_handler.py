import logging
from typing import Any

from redis import Redis

from src.agentic_crypto_influencer.config.key_constants import REDIS_URL
from src.agentic_crypto_influencer.config.redis_constants import (
    ERROR_REDIS_CONNECTION,
    ERROR_REDIS_GET_KEY,
    ERROR_REDIS_KEY_RETRIEVAL,
    ERROR_REDIS_KEY_SET,
    ERROR_REDIS_SET_KEY,
    ERROR_REDIS_URL_MISSING,
    LOG_REDIS_CONNECTED,
    LOG_REDIS_CONNECTION_FAILED,
)


class RedisHandler:
    def __init__(self, lazy_connect: bool = False):
        self.redis_client: Redis[bytes] | None = None
        self.redis_url = REDIS_URL
        self.lazy_connect = lazy_connect

        if not lazy_connect:
            self._connect()

    def _connect(self) -> None:
        """Establish connection to Redis."""
        if not self.redis_url:
            raise ValueError(ERROR_REDIS_URL_MISSING)

        try:
            self.redis_client = Redis.from_url(self.redis_url)
            logging.info(LOG_REDIS_CONNECTED, self.redis_url)
        except Exception as e:
            logging.error(LOG_REDIS_CONNECTION_FAILED, self.redis_url, str(e))
            raise ConnectionError(ERROR_REDIS_CONNECTION) from e

    def _ensure_connected(self) -> None:
        """Ensure Redis connection is established (lazy connection)."""
        if self.redis_client is None:
            self._connect()

    def get(self, key: str) -> bytes | None:
        self._ensure_connected()
        try:
            return self.redis_client.get(key)  # type: ignore[union-attr]
        except Exception as e:
            logging.error(ERROR_REDIS_GET_KEY, key, str(e))
            raise RuntimeError(ERROR_REDIS_KEY_RETRIEVAL % (key, e)) from e

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        self._ensure_connected()
        try:
            self.redis_client.set(key, value, ex=ex)  # type: ignore[union-attr]
        except Exception as e:
            logging.error(ERROR_REDIS_SET_KEY, key, str(e))
            raise RuntimeError(ERROR_REDIS_KEY_SET % (key, e)) from e

    def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        self._ensure_connected()
        try:
            result = self.redis_client.delete(key)  # type: ignore[union-attr]
            return bool(result)
        except Exception as e:
            logging.error("Failed to delete key '%s' from Redis: %s", key, str(e))
            raise RuntimeError(f"Error deleting key '{key}' from Redis: {e!s}") from e

    def ping(self) -> bool:
        """Test Redis connection with ping."""
        self._ensure_connected()
        try:
            result = self.redis_client.ping()  # type: ignore[union-attr]
            return bool(result)
        except Exception as e:
            logging.error("Redis ping failed: %s", str(e))
            raise RuntimeError(f"Redis ping failed: {e!s}") from e
