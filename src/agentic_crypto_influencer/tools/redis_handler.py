import logging
from typing import Any

from redis import Redis
from src.agentic_crypto_influencer.config.key_constants import REDIS_URL


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
            raise ValueError("REDIS_URL must be set in the environment variables.")

        try:
            self.redis_client = Redis.from_url(self.redis_url)
            logging.info("Connected to Redis at %s", self.redis_url)
        except Exception as e:
            logging.error("Failed to connect to Redis at %s: %s", self.redis_url, str(e))
            raise ConnectionError("Could not connect to Redis.") from e

    def _ensure_connected(self) -> None:
        """Ensure Redis connection is established (lazy connection)."""
        if self.redis_client is None:
            self._connect()

    def get(self, key: str) -> bytes | None:
        self._ensure_connected()
        try:
            return self.redis_client.get(key)  # type: ignore
        except Exception as e:
            logging.error("Failed to get key '%s' from Redis: %s", key, str(e))
            raise RuntimeError(f"Error retrieving key '{key}' from Redis: {e!s}") from e

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        self._ensure_connected()
        try:
            self.redis_client.set(key, value, ex=ex)  # type: ignore
        except Exception as e:
            logging.error("Failed to set key '%s' in Redis: %s", key, str(e))
            raise RuntimeError(f"Error setting key '{key}' in Redis: {e!s}") from e
