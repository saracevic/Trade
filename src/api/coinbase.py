"""
Coinbase API Module
Minimal Coinbase Exchange API helpers (public endpoints).
"""

from typing import Any, Dict, List, Optional

from src.api.base import BaseExchangeAPI


class CoinbaseAPI(BaseExchangeAPI):
    """
    Coinbase Exchange API client for cryptocurrency data.

    Provides access to Coinbase Exchange public endpoints for
    product information, statistics, and candlestick data.
    """

    def __init__(self, timeout: int = 20) -> None:
        """
        Initialize Coinbase API client.

        Args:
            timeout: Request timeout in seconds (default: 20)
        """
        super().__init__(base_url="https://api.exchange.coinbase.com", timeout=timeout)

    def get_exchange_info(self) -> List[Dict[str, Any]]:
        """
        Get Coinbase Exchange products information.

        Returns:
            List of product dictionaries containing trading pair information

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self.get_products()

    def get_products(self) -> List[Dict[str, Any]]:
        """
        Get available trading products/pairs on Coinbase.

        Returns:
            List of product information dictionaries

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self._make_request("/products")

    def get_product_stats(self, product_id: str) -> Dict[str, Any]:
        """
        Get 24-hour stats for a product.

        Args:
            product_id: Product identifier (e.g., 'BTC-USD')

        Returns:
            Dictionary containing 24-hour statistics including
            open, high, low, volume, and last price

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self._make_request(f"/products/{product_id}/stats")

    def get_ticker_24h(self) -> List[Dict[str, Any]]:
        """
        Get 24-hour ticker information for all trading pairs.

        Note: Coinbase doesn't have a single endpoint for all tickers.
        This method gets the product list and can be extended to fetch
        individual stats if needed.

        Returns:
            List of product information (can be enhanced with stats)

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self.get_products()

    def get_klines(
        self,
        product_id: str,
        interval: str = "1m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1500,
    ) -> List[List]:
        """
        Get candlestick data for a product.

        Args:
            product_id: Product identifier (e.g., 'BTC-USD')
            interval: Time interval in seconds (60 for 1m, 300 for 5m, etc.)
            start_time: Start timestamp (ISO 8601 or Unix timestamp)
            end_time: End timestamp (ISO 8601 or Unix timestamp)
            limit: Maximum number of candles (not used, included for compatibility)

        Returns:
            List of candle data. Each candle is a list containing:
            [time, low, high, open, close, volume]

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        # Convert interval string to granularity in seconds
        interval_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "6h": 21600,
            "1d": 86400,
        }

        granularity = interval_map.get(interval, 60)

        params: Dict[str, Any] = {"granularity": granularity}

        if start_time is not None:
            params["start"] = start_time
        if end_time is not None:
            params["end"] = end_time

        return self._make_request(f"/products/{product_id}/candles", params=params)


# Legacy function wrappers for backward compatibility
def products() -> List[Dict[str, Any]]:
    """Legacy function: Get products."""
    api = CoinbaseAPI()
    return api.get_products()


def product_stats(product_id: str) -> Dict[str, Any]:
    """Legacy function: Get product stats."""
    api = CoinbaseAPI()
    return api.get_product_stats(product_id)


def klines(
    product_id: str, granularity: int = 60, start: Optional[str] = None, end: Optional[str] = None
) -> List[List]:
    """Legacy function: Get candle data."""
    api = CoinbaseAPI()
    params: Dict[str, Any] = {"granularity": granularity}
    if start is not None:
        params["start"] = start
    if end is not None:
        params["end"] = end
    return api._make_request(f"/products/{product_id}/candles", params=params)
