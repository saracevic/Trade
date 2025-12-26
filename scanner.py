"""
Trade Scanner Module

This module provides comprehensive trading pair scanning functionality across multiple
cryptocurrency exchanges with professional logging, error handling, and configuration management.

Author: Trade Bot Development Team
Date: 2025-12-26
Version: 2.0.0
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
from pathlib import Path


# ============================================================================
# Configuration and Enums
# ============================================================================

class ExchangeType(Enum):
    """Enumeration of supported cryptocurrency exchanges."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BITFINEX = "bitfinex"


@dataclass
class ScannerConfig:
    """
    Configuration dataclass for the trade scanner.
    
    Attributes:
        api_keys (Dict[str, str]): API keys for each exchange
        api_secrets (Dict[str, str]): API secrets for each exchange
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (Optional[str]): Path to log file, None for console only
        min_volume (float): Minimum trading volume filter
        min_price (float): Minimum price filter
        cache_duration (int): Cache duration in seconds
        timeout (int): API request timeout in seconds
        retry_attempts (int): Number of retry attempts for failed requests
        enabled_exchanges (List[str]): List of enabled exchanges to scan
    """
    api_keys: Dict[str, str]
    api_secrets: Dict[str, str]
    log_level: str = "INFO"
    log_file: Optional[str] = None
    min_volume: float = 1000.0
    min_price: float = 0.00001
    cache_duration: int = 300
    timeout: int = 10
    retry_attempts: int = 3
    enabled_exchanges: List[str] = None
    
    def __post_init__(self) -> None:
        """Initialize default enabled exchanges if not provided."""
        if self.enabled_exchanges is None:
            self.enabled_exchanges = [e.value for e in ExchangeType]
    
    @classmethod
    def from_json(cls, json_path: str) -> "ScannerConfig":
        """
        Load configuration from a JSON file.
        
        Args:
            json_path (str): Path to the JSON configuration file
            
        Returns:
            ScannerConfig: Configuration object
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def to_json(self, json_path: str) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            json_path (str): Path where to save the JSON configuration
        """
        with open(json_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)


@dataclass
class TradingPair:
    """
    Represents a trading pair found during scanning.
    
    Attributes:
        symbol (str): Trading pair symbol (e.g., BTC/USD)
        exchange (str): Exchange name
        price (float): Current price
        volume_24h (float): 24-hour trading volume
        bid (Optional[float]): Current bid price
        ask (Optional[float]): Current ask price
        change_24h (Optional[float]): 24-hour price change percentage
        timestamp (datetime): When this pair was scanned
    """
    symbol: str
    exchange: str
    price: float
    volume_24h: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    change_24h: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trading pair to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the trading pair
        """
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'price': self.price,
            'volume_24h': self.volume_24h,
            'bid': self.bid,
            'ask': self.ask,
            'change_24h': self.change_24h,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logger(name: str, config: ScannerConfig) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name (str): Logger name
        config (ScannerConfig): Configuration object containing logging settings
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if configured)
    if config.log_file:
        try:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except IOError as e:
            logger.warning(f"Could not create file handler for {config.log_file}: {e}")
    
    return logger


# ============================================================================
# Exchange Scanner Base Class
# ============================================================================

class ExchangeScanner(ABC):
    """
    Abstract base class for exchange-specific scanners.
    
    This class defines the interface that all exchange implementations must follow,
    ensuring consistency and maintainability across different exchange adapters.
    """
    
    def __init__(self, exchange_name: str, logger: logging.Logger) -> None:
        """
        Initialize the exchange scanner.
        
        Args:
            exchange_name (str): Name of the exchange
            logger (logging.Logger): Logger instance
        """
        self.exchange_name = exchange_name
        self.logger = logger
        self.last_scan_time: Optional[datetime] = None
    
    @abstractmethod
    async def scan(self) -> List[TradingPair]:
        """
        Scan the exchange for trading pairs.
        
        Returns:
            List[TradingPair]: List of discovered trading pairs
            
        Raises:
            Exception: Exchange-specific exceptions
        """
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker information for a specific symbol.
        
        Args:
            symbol (str): Trading pair symbol
            
        Returns:
            Optional[Dict[str, Any]]: Ticker data or None if not found
        """
        pass
    
    def _validate_pair_data(self, pair_data: Dict[str, Any]) -> bool:
        """
        Validate trading pair data.
        
        Args:
            pair_data (Dict[str, Any]): Trading pair data to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        required_fields = ['symbol', 'price', 'volume_24h']
        return all(field in pair_data for field in required_fields)
    
    async def update_scan_time(self) -> None:
        """Update the last scan time to current UTC time."""
        self.last_scan_time = datetime.utcnow()
        self.logger.debug(f"Updated scan time for {self.exchange_name}")


# ============================================================================
# Binance Exchange Scanner
# ============================================================================

class BinanceScanner(ExchangeScanner):
    """
    Scanner implementation for Binance exchange.
    
    Provides methods to scan Binance for trading pairs and retrieve ticker data.
    """
    
    def __init__(self, api_key: str, api_secret: str, logger: logging.Logger) -> None:
        """
        Initialize Binance scanner.
        
        Args:
            api_key (str): Binance API key
            api_secret (str): Binance API secret
            logger (logging.Logger): Logger instance
        """
        super().__init__(ExchangeType.BINANCE.value, logger)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com/api/v3"
        self.logger.info("BinanceScanner initialized")
    
    async def scan(self, filters: Optional[Dict[str, Any]] = None) -> List[TradingPair]:
        """
        Scan Binance for trading pairs.
        
        Args:
            filters (Optional[Dict[str, Any]]): Filter criteria (min_volume, min_price, etc.)
            
        Returns:
            List[TradingPair]: List of discovered trading pairs
        """
        self.logger.info("Starting Binance scan...")
        pairs: List[TradingPair] = []
        
        try:
            # Simulated API call - replace with actual API integration
            self.logger.debug("Fetching trading pairs from Binance")
            await asyncio.sleep(0.1)  # Simulate API latency
            
            # Mock data for demonstration
            mock_pairs = [
                {'symbol': 'BTC/USDT', 'price': 45000.0, 'volume_24h': 1000000.0},
                {'symbol': 'ETH/USDT', 'price': 2500.0, 'volume_24h': 800000.0},
            ]
            
            for pair_data in mock_pairs:
                if self._validate_pair_data(pair_data):
                    pair = TradingPair(
                        symbol=pair_data['symbol'],
                        exchange=self.exchange_name,
                        price=pair_data['price'],
                        volume_24h=pair_data['volume_24h']
                    )
                    pairs.append(pair)
            
            await self.update_scan_time()
            self.logger.info(f"Binance scan completed. Found {len(pairs)} pairs")
            
        except Exception as e:
            self.logger.error(f"Error scanning Binance: {str(e)}", exc_info=True)
            raise
        
        return pairs
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker information from Binance.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Optional[Dict[str, Any]]: Ticker data or None if not found
        """
        self.logger.debug(f"Fetching ticker for {symbol} from Binance")
        
        try:
            # Simulated API call
            await asyncio.sleep(0.05)
            return {
                'symbol': symbol,
                'lastPrice': 45000.0,
                'volume': 1000000.0,
                'priceChangePercent': 2.5
            }
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return None


# ============================================================================
# Coinbase Exchange Scanner
# ============================================================================

class CoinbaseScanner(ExchangeScanner):
    """
    Scanner implementation for Coinbase exchange.
    
    Provides methods to scan Coinbase for trading pairs and retrieve ticker data.
    """
    
    def __init__(self, api_key: str, api_secret: str, logger: logging.Logger) -> None:
        """
        Initialize Coinbase scanner.
        
        Args:
            api_key (str): Coinbase API key
            api_secret (str): Coinbase API secret
            logger (logging.Logger): Logger instance
        """
        super().__init__(ExchangeType.COINBASE.value, logger)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.exchange.coinbase.com"
        self.logger.info("CoinbaseScanner initialized")
    
    async def scan(self, filters: Optional[Dict[str, Any]] = None) -> List[TradingPair]:
        """
        Scan Coinbase for trading pairs.
        
        Args:
            filters (Optional[Dict[str, Any]]): Filter criteria
            
        Returns:
            List[TradingPair]: List of discovered trading pairs
        """
        self.logger.info("Starting Coinbase scan...")
        pairs: List[TradingPair] = []
        
        try:
            self.logger.debug("Fetching trading pairs from Coinbase")
            await asyncio.sleep(0.1)  # Simulate API latency
            
            # Mock data
            mock_pairs = [
                {'symbol': 'BTC-USD', 'price': 45100.0, 'volume_24h': 950000.0},
                {'symbol': 'ETH-USD', 'price': 2510.0, 'volume_24h': 820000.0},
            ]
            
            for pair_data in mock_pairs:
                if self._validate_pair_data(pair_data):
                    pair = TradingPair(
                        symbol=pair_data['symbol'],
                        exchange=self.exchange_name,
                        price=pair_data['price'],
                        volume_24h=pair_data['volume_24h']
                    )
                    pairs.append(pair)
            
            await self.update_scan_time()
            self.logger.info(f"Coinbase scan completed. Found {len(pairs)} pairs")
            
        except Exception as e:
            self.logger.error(f"Error scanning Coinbase: {str(e)}", exc_info=True)
            raise
        
        return pairs
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker information from Coinbase.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC-USD')
            
        Returns:
            Optional[Dict[str, Any]]: Ticker data or None if not found
        """
        self.logger.debug(f"Fetching ticker for {symbol} from Coinbase")
        
        try:
            await asyncio.sleep(0.05)
            return {
                'id': symbol,
                'price': 45100.0,
                'volume': 950000.0,
                'change': 2.3
            }
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return None


# ============================================================================
# Main Trade Scanner Class
# ============================================================================

class TradeScanner:
    """
    Main trade scanner orchestrator.
    
    This class manages scanning operations across multiple exchanges with
    configuration management, caching, error handling, and comprehensive logging.
    
    Attributes:
        config (ScannerConfig): Scanner configuration
        logger (logging.Logger): Logger instance
        scanners (Dict[str, ExchangeScanner]): Exchange-specific scanners
        scan_results (Dict[str, List[TradingPair]]): Cached scan results
        cache_timestamp (Optional[datetime]): When cache was last updated
    """
    
    def __init__(self, config: ScannerConfig) -> None:
        """
        Initialize the trade scanner.
        
        Args:
            config (ScannerConfig): Configuration object
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.logger = setup_logger(__name__, config)
        self.scanners: Dict[str, ExchangeScanner] = {}
        self.scan_results: Dict[str, List[TradingPair]] = {}
        self.cache_timestamp: Optional[datetime] = None
        
        self.logger.info("Initializing TradeScanner")
        self._initialize_scanners()
        self.logger.info("TradeScanner initialization complete")
    
    def _initialize_scanners(self) -> None:
        """
        Initialize exchange-specific scanners based on configuration.
        
        Raises:
            ValueError: If required API credentials are missing
        """
        self.logger.debug("Initializing exchange scanners")
        
        for exchange in self.config.enabled_exchanges:
            try:
                api_key = self.config.api_keys.get(exchange)
                api_secret = self.config.api_secrets.get(exchange)
                
                if not api_key or not api_secret:
                    self.logger.warning(f"Missing credentials for {exchange}")
                    continue
                
                if exchange == ExchangeType.BINANCE.value:
                    self.scanners[exchange] = BinanceScanner(
                        api_key, api_secret, self.logger
                    )
                elif exchange == ExchangeType.COINBASE.value:
                    self.scanners[exchange] = CoinbaseScanner(
                        api_key, api_secret, self.logger
                    )
                else:
                    self.logger.warning(f"Unknown exchange: {exchange}")
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize {exchange} scanner: {str(e)}")
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cached results are still valid.
        
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if not self.cache_timestamp:
            return False
        
        elapsed = (datetime.utcnow() - self.cache_timestamp).total_seconds()
        return elapsed < self.config.cache_duration
    
    async def scan_single_exchange(self, exchange: str) -> List[TradingPair]:
        """
        Scan a single exchange for trading pairs.
        
        Args:
            exchange (str): Exchange name to scan
            
        Returns:
            List[TradingPair]: List of discovered trading pairs
            
        Raises:
            ValueError: If exchange is not supported or not initialized
        """
        self.logger.info(f"Scanning single exchange: {exchange}")
        
        if exchange not in self.scanners:
            raise ValueError(f"Scanner not available for {exchange}")
        
        try:
            scanner = self.scanners[exchange]
            pairs = await scanner.scan()
            
            # Apply filters
            filtered_pairs = self._apply_filters(pairs)
            
            self.scan_results[exchange] = filtered_pairs
            self.logger.info(f"Successfully scanned {exchange}: {len(filtered_pairs)} pairs found")
            
            return filtered_pairs
            
        except Exception as e:
            self.logger.error(f"Error scanning {exchange}: {str(e)}", exc_info=True)
            raise
    
    async def scan_all_exchanges(self) -> Dict[str, List[TradingPair]]:
        """
        Scan all enabled exchanges concurrently.
        
        Returns:
            Dict[str, List[TradingPair]]: Results keyed by exchange name
        """
        self.logger.info("Starting scan of all exchanges")
        
        if self._is_cache_valid():
            self.logger.info("Using cached scan results")
            return self.scan_results
        
        try:
            tasks = [
                self.scan_single_exchange(exchange)
                for exchange in self.scanners.keys()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results
            for exchange, result in zip(self.scanners.keys(), results):
                if isinstance(result, Exception):
                    self.logger.error(f"Exception from {exchange}: {str(result)}")
                    self.scan_results[exchange] = []
            
            self.cache_timestamp = datetime.utcnow()
            self.logger.info("All exchange scans completed")
            
            return self.scan_results
            
        except Exception as e:
            self.logger.error(f"Error during multi-exchange scan: {str(e)}", exc_info=True)
            raise
    
    def _apply_filters(self, pairs: List[TradingPair]) -> List[TradingPair]:
        """
        Apply configured filters to trading pairs.
        
        Args:
            pairs (List[TradingPair]): Trading pairs to filter
            
        Returns:
            List[TradingPair]: Filtered trading pairs
        """
        filtered = [
            pair for pair in pairs
            if pair.volume_24h >= self.config.min_volume
            and pair.price >= self.config.min_price
        ]
        
        self.logger.debug(
            f"Applied filters: {len(pairs)} pairs -> {len(filtered)} pairs"
        )
        
        return filtered
    
    def get_pair_by_symbol(self, symbol: str, exchange: Optional[str] = None) -> Optional[TradingPair]:
        """
        Retrieve a specific trading pair from cached results.
        
        Args:
            symbol (str): Trading pair symbol
            exchange (Optional[str]): Specific exchange, searches all if None
            
        Returns:
            Optional[TradingPair]: Trading pair if found, None otherwise
        """
        if exchange:
            pairs = self.scan_results.get(exchange, [])
            return next((p for p in pairs if p.symbol == symbol), None)
        
        # Search across all exchanges
        for pairs in self.scan_results.values():
            pair = next((p for p in pairs if p.symbol == symbol), None)
            if pair:
                return pair
        
        return None
    
    def get_top_pairs_by_volume(self, limit: int = 10) -> List[Tuple[str, TradingPair]]:
        """
        Get top trading pairs sorted by 24h volume.
        
        Args:
            limit (int): Number of pairs to return
            
        Returns:
            List[Tuple[str, TradingPair]]: Top pairs with exchange names
        """
        all_pairs: List[Tuple[str, TradingPair]] = []
        
        for exchange, pairs in self.scan_results.items():
            all_pairs.extend((exchange, pair) for pair in pairs)
        
        sorted_pairs = sorted(
            all_pairs,
            key=lambda x: x[1].volume_24h,
            reverse=True
        )
        
        self.logger.debug(f"Retrieved top {limit} pairs by volume")
        return sorted_pairs[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current scan results.
        
        Returns:
            Dict[str, Any]: Statistics including count, averages, etc.
        """
        stats = {
            'last_updated': self.cache_timestamp.isoformat() if self.cache_timestamp else None,
            'exchanges_scanned': len(self.scan_results),
            'total_pairs': sum(len(pairs) for pairs in self.scan_results.values()),
            'pairs_by_exchange': {
                exchange: len(pairs)
                for exchange, pairs in self.scan_results.items()
            }
        }
        
        # Calculate average volume and price
        all_pairs = [p for pairs in self.scan_results.values() for p in pairs]
        if all_pairs:
            stats['avg_volume'] = sum(p.volume_24h for p in all_pairs) / len(all_pairs)
            stats['avg_price'] = sum(p.price for p in all_pairs) / len(all_pairs)
        
        self.logger.debug(f"Generated statistics: {stats}")
        return stats
    
    def export_results(self, format: str = "json", filepath: Optional[str] = None) -> str:
        """
        Export scan results in various formats.
        
        Args:
            format (str): Export format ('json', 'csv')
            filepath (Optional[str]): File path to save, returns string if None
            
        Returns:
            str: Exported data as string
            
        Raises:
            ValueError: If format is not supported
        """
        if format == "json":
            data = {
                'timestamp': self.cache_timestamp.isoformat() if self.cache_timestamp else None,
                'results': {
                    exchange: [pair.to_dict() for pair in pairs]
                    for exchange, pairs in self.scan_results.items()
                }
            }
            output = json.dumps(data, indent=2)
            
        elif format == "csv":
            lines = ["symbol,exchange,price,volume_24h,timestamp"]
            for pairs in self.scan_results.values():
                for pair in pairs:
                    lines.append(
                        f"{pair.symbol},{pair.exchange},{pair.price},"
                        f"{pair.volume_24h},{pair.timestamp.isoformat()}"
                    )
            output = "\n".join(lines)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        if filepath:
            Path(filepath).write_text(output)
            self.logger.info(f"Results exported to {filepath}")
        
        return output


# ============================================================================
# Main Entry Point
# ============================================================================

async def main() -> None:
    """
    Main entry point for the trade scanner application.
    
    Demonstrates basic usage of the TradeScanner class.
    """
    # Example configuration
    config = ScannerConfig(
        api_keys={
            'binance': 'your_binance_api_key',
            'coinbase': 'your_coinbase_api_key'
        },
        api_secrets={
            'binance': 'your_binance_api_secret',
            'coinbase': 'your_coinbase_api_secret'
        },
        log_level="INFO",
        min_volume=10000.0,
        min_price=0.01
    )
    
    # Initialize scanner
    scanner = TradeScanner(config)
    
    try:
        # Scan all exchanges
        results = await scanner.scan_all_exchanges()
        
        # Display statistics
        stats = scanner.get_statistics()
        print(f"\nScan Statistics:\n{json.dumps(stats, indent=2)}")
        
        # Get top pairs by volume
        top_pairs = scanner.get_top_pairs_by_volume(5)
        print(f"\nTop 5 pairs by volume:")
        for exchange, pair in top_pairs:
            print(f"  {pair.symbol} on {exchange}: ${pair.price} (Vol: {pair.volume_24h})")
        
        # Export results
        scanner.export_results("json", "scan_results.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
