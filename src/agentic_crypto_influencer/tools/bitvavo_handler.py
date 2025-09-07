from typing import Any

from python_bitvavo_api.bitvavo import Bitvavo

from src.agentic_crypto_influencer.config.app_constants import TOOL_NAME_BITVAVO
from src.agentic_crypto_influencer.config.error_constants import (
    ERROR_CONFIG_MISSING_API_CREDENTIALS,
)
from src.agentic_crypto_influencer.config.key_constants import BITVAVO_API_KEY, BITVAVO_API_SECRET
from src.agentic_crypto_influencer.config.logging_config import LoggerMixin, get_logger
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager
from src.agentic_crypto_influencer.error_management.exceptions import (
    APIConnectionError,
    ConfigurationError,
    ValidationError,
)
from src.agentic_crypto_influencer.error_management.retry import retry
from src.agentic_crypto_influencer.error_management.validator import Validator


class BitvavoHandler(LoggerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.error_manager = ErrorManager()
        self.validator = Validator()

        # Validate API credentials
        try:
            self.validator.validate_string(BITVAVO_API_KEY, "bitvavo_api_key", min_length=1)
            self.validator.validate_string(BITVAVO_API_SECRET, "bitvavo_api_secret", min_length=1)
        except ValidationError as e:
            raise ConfigurationError(ERROR_CONFIG_MISSING_API_CREDENTIALS) from e

        try:
            self.client = Bitvavo({"APIKEY": BITVAVO_API_KEY, "APISECRET": BITVAVO_API_SECRET})
            self.logger.info(f"{TOOL_NAME_BITVAVO} initialized successfully")
        except Exception as e:
            self.error_manager.handle_configuration_error(
                error=e, config_name="Bitvavo API client initialization"
            )

    @retry(max_attempts=3, exceptions=(APIConnectionError,))
    def get_market_data(self, market: str) -> dict[str, Any] | None:
        """Fetch current market data for a specific market."""
        # Validate input
        self.validator.validate_string(market, "market", min_length=1)

        self.logger.debug(f"Fetching market data for {market}")
        try:
            response: dict[str, Any] | None = self.client.tickerPrice({"market": market})
            self.logger.info(f"Successfully fetched market data for {market}")
            return response
        except Exception as e:
            context = {"market": market, "operation": "get_market_data"}
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise APIConnectionError(
                    message=f"Failed to connect to Bitvavo API: {e}",
                    service="Bitvavo",
                    endpoint="tickerPrice",
                ) from e
            self.error_manager.handle_error(e, context=context)
            return None


def main() -> None:
    """Main function for command-line usage."""
    logger = get_logger(__name__)
    logger.info("Starting Bitvavo market data fetch")

    bitvavo = BitvavoHandler()

    # Fetch and log market data for a specific market (e.g., 'BTC-USDC')
    market = "BTC-USDC"
    try:
        market_data = bitvavo.get_market_data(market)
        logger.info(f"Market Data for {market}: {market_data}")
    except RuntimeError as e:
        logger.error(f"Error fetching market data: {e}")


# Example usage:
if __name__ == "__main__":
    main()
