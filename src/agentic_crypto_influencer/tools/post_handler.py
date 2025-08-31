import logging
from typing import Any

import requests

from src.agentic_crypto_influencer.config.key_constants import X_TWEETS_ENDPOINT, X_URL


class PostHandler:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.endpoint = f"{X_URL}{X_TWEETS_ENDPOINT}"

    def post_message(self, post: str) -> dict[str, Any]:
        if not post or len(post) > 280:
            logging.error("Post length invalid: %d", len(post))
            raise ValueError("Post must be between 1 and 280 characters")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": post}
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            logging.info("Post response status: %d", response.status_code)
            if response.status_code != 201:
                logging.error("Request error: %d %s", response.status_code, response.text)
                raise Exception(
                    f"Request returned an error: {response.status_code} {response.text}"
                )
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            logging.error("Post error: %s", str(e))
            raise RuntimeError(f"An error occurred while posting on X. Message: {e!s}") from e
