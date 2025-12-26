"""
Base Exchange API Module
Abstract base class for all exchange API implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging


class BaseExchangeAPI(ABC):
    """
    Abstract base class for cryptocurrency exchange APIs.

    All exchange-specific implementations should inherit from this class
    and implement the required abstract methods.

    Attributes:
        logger: Logger instance for the exchange
        base_url: Base URL for the exchange API
        timeout: Request timeout in seconds
    """

    def __init__(self, base_url: str, timeout: int = 20) -> None:
        """
        Initialize the base exchange API.

        Args:
            base_url: Base URL for the exchange API
            timeout: Request timeout in seconds (default: 20)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including available trading pairs.

        Returns:
            Dictionary containing exchange information

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass

    @abstractmethod
    def get_ticker_24h(self) -> List[Dict[str, Any]]:
        """
        Get 24-hour ticker information for all trading pairs.

        Returns:
            List of ticker information dictionaries

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass

    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        interval: str = '1m',
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1500
    ) -> List[List]:
        """
        Get candlestick/kline data for a trading pair.

        Args:
            symbol: Trading pair symbol
            interval: Time interval (e.g., '1m', '5m', '1h')
            start_time: Start timestamp in milliseconds (optional)
            end_time: End timestamp in milliseconds (optional)
            limit: Number of candles to return (default: 1500)

        Returns:
            List of candle data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry: int = 3
    ) -> Any:
        """
        Make an HTTP request to the exchange API.

        This is a helper method that can be used by subclasses.
        Implements retry logic for failed requests.

        Args:
            endpoint: API endpoint path
            params: Query parameters (optional)
            retry: Number of retry attempts (default: 3)

        Returns:
            Response data (usually JSON)

        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        import requests
        import time

        url = self.base_url + endpoint

        for attempt in range(retry):
            try:
                self.logger.debug(f"Request attempt {attempt + 1}/{retry}: {url}")
                response = requests.get(url, params=params, timeout=self.timeout)

                if response.status_code == 200:
                    return response.json()

                self.logger.warning(
                    f"Request failed with status {response.status_code}, "
                    f"attempt {attempt + 1}/{retry}"
                )

                if attempt < retry - 1:
                    time.sleep(0.3)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error on attempt {attempt + 1}/{retry}: {e}")
                if attempt < retry - 1:
                    time.sleep(0.3)
                else:
                    raise

        # If we get here, all retries failed
        raise requests.exceptions.RequestException(
            f"Failed after {retry} attempts to {url}"
        )
