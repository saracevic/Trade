"""
Binance API Module
Minimal Binance Futures (USDT-M) helper using public endpoints.
"""

from typing import List, Dict, Any, Optional
from src.api.base import BaseExchangeAPI


class BinanceAPI(BaseExchangeAPI):
    """
    Binance Futures API client for cryptocurrency data.
    
    Provides access to Binance Futures (USDT-M) public endpoints
    for exchange information, ticker data, and candlestick charts.
    """
    
    def __init__(self, timeout: int = 20) -> None:
        """
        Initialize Binance API client.
        
        Args:
            timeout: Request timeout in seconds (default: 20)
        """
        super().__init__(base_url="https://fapi.binance.com", timeout=timeout)
        
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get Binance Futures exchange information.
        
        Returns:
            Dictionary containing exchange information including symbols,
            trading rules, and rate limits
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self._make_request('/fapi/v1/exchangeInfo')
    
    def get_ticker_24h(self) -> List[Dict[str, Any]]:
        """
        Get 24-hour ticker information for all trading pairs.
        
        Returns:
            List of ticker data dictionaries containing price, volume,
            and other 24-hour statistics for all trading pairs
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        return self._make_request('/fapi/v1/ticker/24hr')
    
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
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '1h', '1d')
            start_time: Start timestamp in milliseconds (optional)
            end_time: End timestamp in milliseconds (optional)
            limit: Number of candles to return (default: 1500, max: 1500)
            
        Returns:
            List of kline data, each kline is a list containing:
            [open_time, open, high, low, close, volume, close_time, ...]
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        
        if start_time is not None:
            params['startTime'] = int(start_time)
        if end_time is not None:
            params['endTime'] = int(end_time)
            
        return self._make_request('/fapi/v1/klines', params=params)
    
    def get_klines_range(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int
    ) -> List[List]:
        """
        Fetch klines in batches until reaching end_ms.
        
        This method handles pagination automatically, fetching klines
        in batches of 1500 (Binance's maximum) until all data is retrieved.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '1h', '1d')
            start_ms: Start timestamp in milliseconds
            end_ms: End timestamp in milliseconds
            
        Returns:
            List of all kline data within the specified time range
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        import time
        
        data: List[List] = []
        cur = int(start_ms)
        
        while cur < end_ms:
            batch = self.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=cur,
                end_time=end_ms,
                limit=1500
            )
            
            if not batch:
                break
                
            data.extend(batch)
            last_open = batch[-1][0]
            
            # Advance by one ms after last open to avoid duplicate
            cur = int(last_open) + 1
            
            # Rate limiting
            time.sleep(0.12)
            
            # Safety check: if we got less than 1500, we're done
            if len(batch) < 1500:
                break
                
        return data


# Legacy function wrappers for backward compatibility
def exchange_info() -> Dict[str, Any]:
    """Legacy function: Get exchange information."""
    api = BinanceAPI()
    return api.get_exchange_info()


def ticker_24h() -> List[Dict[str, Any]]:
    """Legacy function: Get 24h ticker data."""
    api = BinanceAPI()
    return api.get_ticker_24h()


def klines(
    symbol: str,
    interval: str = '1m',
    startTime: Optional[int] = None,
    endTime: Optional[int] = None,
    limit: int = 1500
) -> List[List]:
    """Legacy function: Get kline data."""
    api = BinanceAPI()
    return api.get_klines(symbol, interval, startTime, endTime, limit)


def klines_range(symbol: str, interval: str, start_ms: int, end_ms: int) -> List[List]:
    """Legacy function: Get kline data in range."""
    api = BinanceAPI()
    return api.get_klines_range(symbol, interval, start_ms, end_ms)
