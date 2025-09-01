import logging
from typing import TYPE_CHECKING

from src.agentic_crypto_influencer.config.key_constants import GOOGLE_API_KEY
from src.agentic_crypto_influencer.config.logging_config import LoggerMixin, get_logger
from src.agentic_crypto_influencer.config.model_constants import MODEL_ID
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager

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
        if not google_genai_available:
            self.logger.error("Google GenAI library is not installed")
            raise ImportError("Google GenAI library is not installed.")

        self.api_key = GOOGLE_API_KEY

        if not self.api_key:
            self.logger.error("Google API key is missing")
            raise ValueError("Google API key is missing")
        
        self.logger.info("GoogleGroundingTool initialized successfully")

    def run_crypto_search(self, query: str) -> str:
        if not query or query.isspace():
            raise ValueError("Query cannot be empty")

        client = genai.Client()

        logging.info(f"Initiating Google API call with query: {query}")

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=query,
                config=GenerateContentConfig(tools=[Tool(google_search=GoogleSearch())]),
            )

            if not response or not response.text:
                raise ValueError("No valid response received from Google API")
        except Exception as e:
            raise RuntimeError(f"Google API request failed: {e!s}") from e

        return str(response.text)


def main() -> None:
    """Main function for command-line usage."""
    logger = get_logger(__name__)
    error_manager = ErrorManager()
    
    try:
        logger.info("Starting Google Grounding Tool search")
        tool = GoogleGroundingTool()
        search_query = "Search query"
        result = tool.run_crypto_search(search_query)
        logger.info("Search Results", extra={"result": result})

    except (ValueError, RuntimeError) as e:
        error_message = error_manager.handle_error(e)
        logger.error(f"Tool error: {error_message}")
    except Exception as e:
        error_message = error_manager.handle_error(e)
        logger.critical(f"Unexpected error: {error_message}")


# Example usage:
if __name__ == "__main__":
    main()
