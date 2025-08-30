import logging

from config.key_constants import GOOGLE_API_KEY
from config.model_constants import MODEL_ID
from error_management.error_manager import ErrorManager

# Conditional imports for optional dependencies
try:
    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

    google_genai_available = True
except ImportError:
    google_genai_available = False
    genai = None
    GenerateContentConfig = None
    GoogleSearch = None
    Tool = None


class GoogleGroundingTool:
    def __init__(self):
        if not google_genai_available:
            raise ImportError(
                "Google GenAI library is not installed. Please install it with: pip install google-genai"
            )

        self.api_key = GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError("Google API key is missing")

    def run_crypto_search(self, query: str) -> str:
        if not query or query.isspace():
            raise ValueError()

        client = genai.Client()

        logging.info(f"Initiating Google API call with query: {query}")

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=query,
                config=GenerateContentConfig(
                    tools=[Tool(google_search=GoogleSearch())]
                ),
            )

            if not response or not response.text:
                raise ValueError("No valid response received from Google API")
        except Exception as e:
            raise RuntimeError(f"Google API request failed: {str(e)}")

        return response.text


def main():
    """Main function for command-line usage."""
    error_manager = ErrorManager()
    try:
        tool = GoogleGroundingTool()
        search_query = "Search query"
        result = tool.run_crypto_search(search_query)
        print("--- Results ---")
        print(result)

    except (ValueError, RuntimeError) as e:
        error_message = error_manager.handle_error(e)
        print(error_message)
    except Exception as e:
        error_message = error_manager.handle_error(e)
        print(error_message)


# Example usage:
if __name__ == "__main__":
    main()
