"""
Module for posting messages to X (Twitter) using OAuth2 authentication.
Handles access token refresh and error management.
"""

import logging
from typing import Any

from src.agentic_crypto_influencer.config.logging_config import LoggerMixin, get_logger
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


class X(LoggerMixin):
    """
    Class for interacting with the X (Twitter) API.

    Handles authentication, token refresh, and posting messages.
    """

    def __init__(self) -> None:
        """
        Initialize X API client.
        """
        super().__init__()
        # Check if required dependencies are available
        if RedisHandler is None:
            self.logger.error("RedisHandler is not available")
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

        # Don't immediately refresh token during init - do it lazily when needed
        self.access_token: dict[str, Any] | None = None
        self.post_handler: Any | None = (
            None  # PostHandler | None but can't type due to conditional import
        )
        self.trends_handler: Any | None = (
            None  # TrendsHandler | None but can't type due to conditional import
        )

        logging.basicConfig(level=logging.INFO)

    def _ensure_token_initialized(self) -> None:
        """Lazily initialize the access token and handlers if not already done."""
        if self.access_token is None:
            try:
                if PostHandler is None or TrendsHandler is None:
                    raise RuntimeError("Required X API dependencies not available")

                self.access_token = self.oauth_handler.refresh_access_token()
                access_token_str = self.access_token.get("access_token", "")
                if not access_token_str:
                    raise RuntimeError("Access token is missing or invalid.")
                self.post_handler = PostHandler(access_token_str)
                self.trends_handler = TrendsHandler(access_token_str)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize X authentication: {e}") from e

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
        self._ensure_token_initialized()
        if self.post_handler is None:  # Safe check instead of assert
            raise RuntimeError("Failed to initialize post handler")
        return self.post_handler.post_message(post)  # type: ignore[no-untyped-call,no-any-return]

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
        self._ensure_token_initialized()
        if self.trends_handler is None:  # Safe check instead of assert
            raise RuntimeError("Failed to initialize trends handler")
        return self.trends_handler.get_personalized_trends(user_id, max_results, exclude)  # type: ignore[no-untyped-call,no-any-return]


def main() -> None:
    """
    Main entry point for posting a message to X.
    Handles error management and logs results.
    """
    logger = get_logger(__name__)
    error_manager = ErrorManager()

    try:
        logger.info("Starting X posting workflow")
        x = X()
        post = "Post"
        result: dict[str, Any] = x.post(post)
        logger.info("Post Results", extra={"result": result})

        # Try fetching personalized trends if user id provided via env
        user_id = X_USER_ID
        if user_id:
            try:
                trends = x.get_personalized_trends(user_id=user_id, max_results=10)
                logger.info("Personalized Trends", extra={"trends": trends})
            except Exception as e:
                logger.error(f"Failed to fetch personalized trends: {e}")
                # Surface via error manager as well
                error_message = error_manager.handle_error(e)
                logger.error(f"Error manager response: {error_message}")
        else:
            logger.info("X_USER_ID not set; skipping personalized trends fetch")
    except (ValueError, RuntimeError) as e:
        error_message = error_manager.handle_error(e)
        logger.error(f"Workflow error: {error_message}")
    except Exception as e:
        error_message = error_manager.handle_error(e)
        logger.critical(f"Unexpected error: {error_message}")


if __name__ == "__main__":
    main()
