from typing import TYPE_CHECKING

from src.agentic_crypto_influencer.config.key_constants import GOOGLE_API_KEY
from src.agentic_crypto_influencer.config.logging_config import LoggerMixin, get_logger
from src.agentic_crypto_influencer.config.model_constants import MODEL_ID
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager
from src.agentic_crypto_influencer.error_management.exceptions import (
    APIConnectionError,
    APITimeoutError,
    ConfigurationError,
    ValidationError,
)
from src.agentic_crypto_influencer.error_management.retry import retry
from src.agentic_crypto_influencer.error_management.validator import Validator

# Conditional imports for optional dependencies
try:
    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

    google_genai_available = True
except ImportError:
    google_genai_available = False

if TYPE_CHECKING:
    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool


class GoogleGroundingTool(LoggerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.error_manager = ErrorManager()
        self.validator = Validator()

        if not google_genai_available:
            self.logger.error("Google GenAI library is not installed")
            raise ConfigurationError("Google GenAI library is not installed")

        # Validate API key
        try:
            self.validator.validate_string(GOOGLE_API_KEY, "google_api_key", min_length=1)
            self.api_key = GOOGLE_API_KEY
        except ValidationError as e:
            raise ConfigurationError("Google API key is missing or invalid") from e

        self.logger.info("GoogleGroundingTool initialized successfully")

    @retry(max_attempts=3, exceptions=(APIConnectionError, APITimeoutError))
    def run_crypto_search(self, query: str) -> str:
        # Validate input
        self.validator.validate_string(query, "search_query", min_length=1)

        client = genai.Client()
        self.logger.info(f"Initiating Google API call with query: {query}")

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=query,
                config=GenerateContentConfig(tools=[Tool(google_search=GoogleSearch())]),
            )

            if not response or not response.text:
                raise ValidationError(
                    message="No valid response received from Google API",
                    field="api_response",
                    value="",
                )

        except Exception as e:
            context = {"query": query, "model": MODEL_ID, "operation": "generate_content"}

            # Categorize different types of API errors
            error_str = str(e).lower()
            if "timeout" in error_str or "deadline" in error_str:
                raise APITimeoutError(
                    message=f"Google API request timed out: {e}",
                    service="Google GenAI",
                    endpoint="generate_content",
                    timeout=30.0,
                ) from e
            elif "connection" in error_str or "network" in error_str:
                raise APIConnectionError(
                    message=f"Failed to connect to Google API: {e}",
                    service="Google GenAI",
                    endpoint="generate_content",
                ) from e
            else:
                self.error_manager.handle_error(e, context=context)
                raise

        return str(response.text)


def main() -> None:
    """Main function for command-line usage."""
    logger = get_logger(__name__)
    error_manager = ErrorManager()

    try:
        logger.info("Starting Google Grounding Tool search")
        tool = GoogleGroundingTool()
        search_query = "Latest Bitcoin price and market trends"
        result = tool.run_crypto_search(search_query)
        logger.info("Search Results", extra={"result": result})

    except ConfigurationError as e:
        error_manager.handle_configuration_error(e, "Google Grounding Tool setup")
        logger.error(f"Configuration error: {e}")
    except (ValidationError, APIConnectionError, APITimeoutError) as e:
        error_manager.handle_error(e)
        logger.error(f"Tool error: {e}")
    except Exception as e:
        error_manager.handle_error(e)
        logger.critical(f"Unexpected error: {e}")
        raise


# Example usage:
if __name__ == "__main__":
    main()
