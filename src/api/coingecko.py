"""
CoinGecko API Module
Provides access to CoinGecko free API endpoints.
"""

from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CoinGeckoAPI:
    """CoinGecko API client for cryptocurrency data."""

    BASE_URL = "https://api.coingecko.com/api/v3"
    TIMEOUT = 20

    @staticmethod
    def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request to CoinGecko API.

        Args:
            path: API endpoint path
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            requests.exceptions.RequestException: On request failure
        """
        url = f"{CoinGeckoAPI.BASE_URL}{path}"
        logger.debug(f"GET {url}")

        response = requests.get(url, params=params, timeout=CoinGeckoAPI.TIMEOUT)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def get_coins_markets(
        vs_currency: str = "usd", per_page: int = 250, page: int = 1, order: str = "market_cap_desc"
    ) -> List[Dict[str, Any]]:
        """
        Get top cryptocurrencies by market cap.

        Args:
            vs_currency: Target currency (default: usd)
            per_page: Number of results per page
            page: Page number
            order: Ordering (market_cap_desc, gecko_desc, gecko_asc, market_cap_asc, market_cap_desc, volume_asc, volume_desc)

        Returns:
            List of market data
        """
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
        }

        logger.info(f"Fetching markets: {per_page} coins, page {page}")
        return CoinGeckoAPI._get("/coins/markets", params=params)

    @staticmethod
    def get_market_chart_range(
        coin_id: str, vs_currency: str, from_ts: int, to_ts: int
    ) -> Dict[str, Any]:
        """
        Get market chart data for a coin over a time range.

        Args:
            coin_id: CoinGecko coin ID
            vs_currency: Target currency
            from_ts: Start timestamp (seconds)
            to_ts: End timestamp (seconds)

        Returns:
            Market chart data
        """
        params = {"vs_currency": vs_currency, "from": int(from_ts), "to": int(to_ts)}

        logger.info(f"Fetching market chart for {coin_id}")
        return CoinGeckoAPI._get(f"/coins/{coin_id}/market_chart/range", params=params)

    @staticmethod
    def map_coin_to_perp(exchange_api: Any, coin_symbol: str) -> List[str]:
        """
        Try to map a base coin symbol to perpetual symbols on an exchange.

        Args:
            exchange_api: Exchange API object (Binance, Coinbase, or Kraken)
            coin_symbol: Base coin symbol (e.g., BTC)

        Returns:
            List of matching perpetual symbols
        """
        candidates: List[str] = []
        coin_symbol = coin_symbol.upper()

        # Try Binance-style exchange_info()
        try:
            info = exchange_api.get_exchange_info()
            symbols = None

            if isinstance(info, dict):
                symbols = info.get("symbols") or info.get("symbolsList")
            elif isinstance(info, list):
                symbols = info

            if symbols and isinstance(symbols, list):
                for s in symbols:
                    sym = None

                    if isinstance(s, dict):
                        sym = s.get("symbol") or s.get("pair")
                    elif isinstance(s, str):
                        sym = s

                    if not sym:
                        continue

                    usdt_like = ("USDT" in sym.upper()) or ("USD" in sym.upper())

                    if sym.upper().startswith(coin_symbol) and usdt_like:
                        # Prefer perpetual contract if available
                        if isinstance(s, dict):
                            contract_type = s.get("contractType") or s.get("type") or ""
                            if contract_type and "PERP" in str(contract_type).upper():
                                candidates.append(sym.upper())
                                continue

                        candidates.append(sym.upper())

        except Exception as e:
            logger.warning(f"Error fetching exchange_info: {e}")

        # Try Coinbase-style products()
        try:
            prods = None

            if hasattr(exchange_api, "get_products"):
                prods = exchange_api.get_products()
            elif hasattr(exchange_api, "products"):
                prods = exchange_api.products()

            if isinstance(prods, list):
                for p in prods:
                    sym = None

                    if isinstance(p, dict):
                        sym = p.get("id") or p.get("symbol") or p.get("name")
                    elif isinstance(p, str):
                        sym = p

                    if not sym:
                        continue

                    su = sym.upper()
                    if su.startswith(coin_symbol) and ("USDT" in su or "USD" in su):
                        candidates.append(su)

        except Exception as e:
            logger.warning(f"Error fetching products: {e}")

        # Remove duplicates while preserving order
        seen = set()
        result: List[str] = []

        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                result.append(candidate)

        logger.info(f"Found {len(result)} perpetual symbols for {coin_symbol}")
        return result
