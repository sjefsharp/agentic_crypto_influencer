from python_bitvavo_api.bitvavo import Bitvavo  # type: ignore
from typing import Any, Dict, Optional

from config.key_constants import BITVAVO_API_KEY, BITVAVO_API_SECRET


class BitvavoHandler:
    def __init__(self):
        self.client = Bitvavo(
            {"APIKEY": BITVAVO_API_KEY, "APISECRET": BITVAVO_API_SECRET}
        )

    def get_market_data(self, market: str) -> Optional[Dict[str, Any]]:
        """Fetch current market data for a specific market."""
        try:
            response: Optional[Dict[str, Any]] = self.client.tickerPrice(  # type: ignore
                {"market": market}
            )  # type: ignore
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to fetch market data: {str(e)}")


# Example usage:
if __name__ == "__main__":
    bitvavo = BitvavoHandler()

    # Fetch and print market data for a specific market (e.g., 'BTC-USDC')
    market = "BTC-USDC"
    try:
        market_data = bitvavo.get_market_data(market)
        print(f"Market Data for {market}:", market_data)
    except RuntimeError as e:
        print(e)
