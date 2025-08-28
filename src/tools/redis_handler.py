import logging
from typing import Any, Optional

from redis import Redis

from config.key_constants import REDIS_URL


class RedisHandler:
    def __init__(self):
        redis_url = REDIS_URL
        if not redis_url:
            raise ValueError("REDIS_URL must be set in the environment variables.")

        try:
            self.redis_client: Redis[bytes] = Redis.from_url(redis_url)
            logging.info("Connected to Redis at %s", redis_url)
        except Exception as e:
            logging.error("Failed to connect to Redis at %s: %s", redis_url, str(e))
            raise ConnectionError("Could not connect to Redis.")

    def get(self, key: str) -> Optional[bytes]:
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logging.error("Failed to get key '%s' from Redis: %s", key, str(e))
            raise RuntimeError(f"Error retrieving key '{key}' from Redis: {str(e)}")

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        try:
            self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logging.error("Failed to set key '%s' in Redis: %s", key, str(e))
            raise RuntimeError(f"Error setting key '{key}' in Redis: {str(e)}")
