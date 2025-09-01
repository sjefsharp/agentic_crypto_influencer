from typing import Any

from python_bitvavo_api.bitvavo import Bitvavo  # type: ignore[import-untyped]

from src.agentic_crypto_influencer.config.key_constants import BITVAVO_API_KEY, BITVAVO_API_SECRET
from src.agentic_crypto_influencer.config.logging_config import LoggerMixin, get_logger


class BitvavoHandler(LoggerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.client = Bitvavo({"APIKEY": BITVAVO_API_KEY, "APISECRET": BITVAVO_API_SECRET})
        self.logger.info("BitvavoHandler initialized")

    def get_market_data(self, market: str) -> dict[str, Any] | None:
        """Fetch current market data for a specific market."""
        self.logger.debug(f"Fetching market data for {market}")
        try:
            response: dict[str, Any] | None = self.client.tickerPrice({"market": market})  # type: ignore[no-untyped-call]
            self.logger.info(f"Successfully fetched market data for {market}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to fetch market data for {market}: {e}")
            raise RuntimeError(f"Failed to fetch market data: {e!s}") from e


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
