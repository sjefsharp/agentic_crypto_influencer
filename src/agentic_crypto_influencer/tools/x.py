"""
Module for posting messages to X (Twitter) using OAuth2 authentication.
Handles access token refresh and error management.
"""

import logging
from typing import Any

from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager

# Import tools with external dependencies conditionally
try:
    from src.agentic_crypto_influencer.tools.oauth_handler import OAuthHandler
except ImportError:
    OAuthHandler = None  # type: ignore

try:
    from src.agentic_crypto_influencer.tools.post_handler import PostHandler
except ImportError:
    PostHandler = None  # type: ignore

try:
    from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler
except ImportError:
    RedisHandler = None  # type: ignore

try:
    from src.agentic_crypto_influencer.tools.trends_handler import TrendsHandler
except ImportError:
    TrendsHandler = None  # type: ignore

from src.agentic_crypto_influencer.config.key_constants import X_USER_ID


class X:
    """
    Class for interacting with the X (Twitter) API.

    Handles authentication, token refresh, and posting messages.
    """

    def __init__(self) -> None:
        """
        Initialize X API client.
        """
        # Check if required dependencies are available
        if RedisHandler is None:
            raise ImportError(
                "RedisHandler is not available. Please install required dependencies."
            )
        if OAuthHandler is None:
            raise ImportError(
                "OAuthHandler is not available. Please install required dependencies."
            )
        if PostHandler is None:
            raise ImportError(
                "PostHandler is not available. Please install required dependencies."
            )
        if TrendsHandler is None:
            raise ImportError(
                "TrendsHandler is not available. Please install required dependencies."
            )

        # Initialize Redis client (lazy connection)
        self.redis_client: Any | None = RedisHandler(lazy_connect=True).redis_client

        self.oauth_handler = OAuthHandler()
        self.access_token = self.oauth_handler.refresh_access_token()
        access_token_str = self.access_token.get("access_token", "")
        if not access_token_str:
            raise RuntimeError("Access token is missing or invalid.")
        self.post_handler = PostHandler(access_token_str)
        self.trends_handler = TrendsHandler(access_token_str)

        logging.basicConfig(level=logging.INFO)

    def post(self, post: str) -> dict[str, Any]:
        """
        Post a message to X (Twitter).

        Args:
            post (str): The message to post. Must be 1-280 characters.

        Returns:
            dict: The JSON response from the X API.

        Raises:
            ValueError: If the post is empty or too long.
            RuntimeError: If posting fails.
            Exception: If the API returns a non-201 status code.
        """
        return self.post_handler.post_message(post)

    def get_personalized_trends(
        self, user_id: str, max_results: int = 10, exclude: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Fetch personalized trends for a user from the X API.

        Args:
            user_id (str): The X user id to fetch personalized trends for.
            max_results (int): Maximum number of trend results to return.
            exclude (Optional[List[str]]): Optional list of trend types to exclude.

        Returns:
            Dict[str, Any]: Parsed JSON response from the trends endpoint.

        Raises:
            RuntimeError: For network/refresh errors.
            Exception: For non-200 responses.
        """
        return self.trends_handler.get_personalized_trends(user_id, max_results, exclude)


def main() -> None:
    """
    Main entry point for posting a message to X.
    Handles error management and prints results.
    """
    error_manager = ErrorManager()
    try:
        x = X()
        post = "Post"
        result: dict[str, Any] = x.post(post)
        print("--- Post Results ---")
        print(result)

        # Try fetching personalized trends if user id provided via env
        user_id = X_USER_ID
        if user_id:
            try:
                trends = x.get_personalized_trends(user_id=user_id, max_results=10)
                print("--- Personalized Trends ---")
                print(trends)
            except Exception as e:
                logging.error("Failed to fetch personalized trends: %s", str(e))
                # Surface via error manager as well
                print(error_manager.handle_error(e))
        else:
            logging.info("X_USER_ID not set; skipping personalized trends fetch")
    except (ValueError, RuntimeError) as e:
        error_message = error_manager.handle_error(e)
        print(error_message)
    except Exception as e:
        error_message = error_manager.handle_error(e)
        print(error_message)


if __name__ == "__main__":
    main()
