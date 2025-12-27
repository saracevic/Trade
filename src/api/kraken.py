"""
Kraken API Module
Minimal Kraken public API helpers.
"""

from typing import Any, Dict, List, Optional

from src.api.base import BaseExchangeAPI


class KrakenAPI(BaseExchangeAPI):
    """
    Kraken API client for cryptocurrency data.

    Provides access to Kraken public endpoints for asset pair
    information and OHLC (candlestick) data.
    """

    def __init__(self, timeout: int = 20) -> None:
        """
        Initialize Kraken API client.

        Args:
            timeout: Request timeout in seconds (default: 20)
        """
        super().__init__(base_url="https://api.kraken.com", timeout=timeout)

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get Kraken exchange asset pairs information.

        Returns:
            Dictionary containing asset pair information

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self.get_asset_pairs()

    def get_asset_pairs(self) -> Dict[str, Any]:
        """
        Get available trading asset pairs on Kraken.

        Returns:
            Dictionary containing asset pair information

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self._make_request("/0/public/AssetPairs")

    def get_ticker(self, pair: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ticker information for one or more trading pairs.

        Args:
            pair: Trading pair(s) to get ticker for. Can be a single pair
                  or comma-separated list. If None, returns all tickers.

        Returns:
            Dictionary containing ticker information including price,
            volume, and other statistics

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        params = {}
        if pair is not None:
            params["pair"] = pair
        return self._make_request("/0/public/Ticker", params=params)

    def get_ticker_24h(self) -> List[Dict[str, Any]]:
        """
        Get 24-hour ticker information for all trading pairs.

        Note: Kraken doesn't have a single endpoint for all tickers.
        This returns the asset pairs list.

        Returns:
            List derived from asset pairs information

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        pairs_data = self.get_asset_pairs()
        # Convert to list format for consistency
        if isinstance(pairs_data, dict) and "result" in pairs_data:
            return [{"pair": k, **v} for k, v in pairs_data["result"].items()]
        return []

    def get_klines(
        self,
        pair: str,
        interval: str = "1m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1500,
    ) -> List[List]:
        """
        Get OHLC (candlestick) data for a trading pair.

        Args:
            pair: Trading pair (e.g., 'XXBTZUSD' for BTC/USD)
            interval: Time interval (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
            start_time: Start timestamp (optional, not directly supported)
            end_time: End timestamp (optional, not directly supported)
            limit: Number of candles (not directly supported, included for compatibility)

        Returns:
            List of OHLC data

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        # Convert interval string to Kraken interval (in minutes)
        interval_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }

        kraken_interval = interval_map.get(interval, 1)

        params = {"pair": pair, "interval": kraken_interval}

        if start_time is not None:
            params["since"] = start_time

        return self.get_ohlc(pair, kraken_interval, start_time)

    def get_ohlc(self, pair: str, interval: int = 1, since: Optional[int] = None) -> List[List]:
        """
        Get OHLC data from Kraken.

        Args:
            pair: Trading pair
            interval: Time frame interval in minutes
            since: Return data since given ID (optional)

        Returns:
            OHLC data from Kraken API

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        params: Dict[str, Any] = {"pair": pair, "interval": interval}

        if since is not None:
            params["since"] = since

        data = self._make_request("/0/public/OHLC", params=params)

        # Extract the actual OHLC data from Kraken's response format
        if isinstance(data, dict) and "result" in data:
            # Kraken returns result with pair name as key
            for key, value in data["result"].items():
                if key != "last" and isinstance(value, list):
                    return value

        return []


# Legacy function wrappers for backward compatibility
def asset_pairs() -> Dict[str, Any]:
    """Legacy function: Get asset pairs."""
    api = KrakenAPI()
    return api.get_asset_pairs()


def ohlc(pair: str, interval: int = 1, since: Optional[int] = None) -> Dict[str, Any]:
    """Legacy function: Get OHLC data."""
    api = KrakenAPI()
    params: Dict[str, Any] = {"pair": pair, "interval": interval}
    if since is not None:
        params["since"] = since
    return api._make_request("/0/public/OHLC", params=params)
