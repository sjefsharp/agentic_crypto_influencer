from typing import Any

from python_bitvavo_api.bitvavo import Bitvavo

from src.agentic_crypto_influencer.config.key_constants import BITVAVO_API_KEY, BITVAVO_API_SECRET


class BitvavoHandler:
    def __init__(self) -> None:
        self.client = Bitvavo({"APIKEY": BITVAVO_API_KEY, "APISECRET": BITVAVO_API_SECRET})

    def get_market_data(self, market: str) -> dict[str, Any] | None:
        """Fetch current market data for a specific market."""
        try:
            response: dict[str, Any] | None = self.client.tickerPrice({"market": market})
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to fetch market data: {e!s}") from e


def main() -> None:
    """Main function for command-line usage."""
    bitvavo = BitvavoHandler()

    # Fetch and print market data for a specific market (e.g., 'BTC-USDC')
    market = "BTC-USDC"
    try:
        market_data = bitvavo.get_market_data(market)
        print(f"Market Data for {market}:", market_data)
    except RuntimeError as e:
        print(e)


# Example usage:
if __name__ == "__main__":
    main()
