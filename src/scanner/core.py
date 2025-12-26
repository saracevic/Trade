"""
Core Scanner Module
Main trade scanner implementation with multi-exchange support.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from src.models.trade import TradingPair, ScannerConfig, ScanResult
from src.utils.logger import setup_logger, LoggerMixin
from src.api.binance import BinanceAPI
from src.api.coinbase import CoinbaseAPI  
from src.api.kraken import KrakenAPI


class TradeScanner(LoggerMixin):
    """
    Main trade scanner orchestrator.
    
    Manages scanning operations across multiple cryptocurrency exchanges with
    configuration management, caching, error handling, and comprehensive logging.
    
    Attributes:
        config: Scanner configuration
        apis: Dictionary of exchange API instances
        scan_results: Cached scan results by exchange
        cache_timestamp: When cache was last updated
    """
    
    def __init__(self, config: ScannerConfig) -> None:
        """
        Initialize the trade scanner.
        
        Args:
            config: Scanner configuration object
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.apis: Dict[str, Any] = {}
        self.scan_results: Dict[str, List[TradingPair]] = {}
        self.cache_timestamp: Optional[datetime] = None
        
        # Set up logging
        self._setup_logging()
        
        self.logger.info("Initializing TradeScanner")
        self._initialize_apis()
        self.logger.info("TradeScanner initialization complete")
    
    def _setup_logging(self) -> None:
        """Configure logging for the scanner."""
        # The LoggerMixin provides self.logger automatically
        # But we can reconfigure it with config settings
        import logging
        logger = logging.getLogger(self.__class__.__module__)
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
    
    def _initialize_apis(self) -> None:
        """
        Initialize exchange API instances based on configuration.
        
        Creates API instances for each enabled exchange that has
        valid credentials configured.
        """
        self.logger.debug("Initializing exchange APIs")
        
        for exchange in self.config.enabled_exchanges:
            try:
                api_key = self.config.api_keys.get(exchange, "")
                api_secret = self.config.api_secrets.get(exchange, "")
                
                # For now, we initialize APIs without requiring keys
                # Most public endpoints don't need authentication
                if exchange == "binance":
                    self.apis[exchange] = BinanceAPI(timeout=self.config.timeout)
                elif exchange == "coinbase":
                    self.apis[exchange] = CoinbaseAPI(timeout=self.config.timeout)
                elif exchange == "kraken":
                    self.apis[exchange] = KrakenAPI(timeout=self.config.timeout)
                else:
                    self.logger.warning(f"Unknown exchange: {exchange}")
                    continue
                
                self.logger.info(f"Initialized {exchange} API")
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize {exchange} API: {str(e)}")
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cached results are still valid.
        
        Returns:
            True if cache is valid and not expired, False otherwise
        """
        if not self.cache_timestamp:
            return False
        
        elapsed = (datetime.utcnow() - self.cache_timestamp).total_seconds()
        is_valid = elapsed < self.config.cache_duration
        
        if is_valid:
            self.logger.debug(f"Cache is valid (age: {elapsed:.1f}s)")
        else:
            self.logger.debug(f"Cache expired (age: {elapsed:.1f}s)")
        
        return is_valid
    
    async def scan_single_exchange(
        self,
        exchange: str
    ) -> ScanResult:
        """
        Scan a single exchange for trading pairs.
        
        Args:
            exchange: Exchange name to scan
            
        Returns:
            ScanResult containing discovered trading pairs and metadata
            
        Raises:
            ValueError: If exchange is not supported or not initialized
        """
        self.logger.info(f"Scanning single exchange: {exchange}")
        start_time = datetime.utcnow()
        
        if exchange not in self.apis:
            raise ValueError(f"API not available for {exchange}")
        
        try:
            api = self.apis[exchange]
            
            # For now, we'll get basic ticker information
            # This can be extended with more complex logic
            if exchange == "binance":
                tickers = await asyncio.to_thread(api.get_ticker_24h)
                pairs = self._parse_binance_tickers(tickers)
            elif exchange == "coinbase":
                products = await asyncio.to_thread(api.get_products)
                pairs = self._parse_coinbase_products(products)
            elif exchange == "kraken":
                asset_pairs = await asyncio.to_thread(api.get_asset_pairs)
                pairs = self._parse_kraken_pairs(asset_pairs)
            else:
                pairs = []
            
            # Apply filters
            filtered_pairs = self._apply_filters(pairs)
            
            # Store results
            self.scan_results[exchange] = filtered_pairs
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Successfully scanned {exchange}: "
                f"{len(filtered_pairs)} pairs found in {duration:.2f}s"
            )
            
            return ScanResult(
                exchange=exchange,
                pairs=filtered_pairs,
                duration=duration,
                success=True
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"Error scanning {exchange}: {str(e)}", exc_info=True)
            
            return ScanResult(
                exchange=exchange,
                pairs=[],
                duration=duration,
                success=False,
                error=str(e)
            )
    
    async def scan_all_exchanges(self) -> Dict[str, ScanResult]:
        """
        Scan all enabled exchanges concurrently.
        
        Returns:
            Dictionary mapping exchange names to scan results
        """
        self.logger.info("Starting scan of all exchanges")
        
        if self._is_cache_valid():
            self.logger.info("Using cached scan results")
            # Convert cached results to ScanResult objects
            return {
                exchange: ScanResult(
                    exchange=exchange,
                    pairs=pairs,
                    duration=0.0,
                    success=True
                )
                for exchange, pairs in self.scan_results.items()
            }
        
        try:
            # Scan all exchanges concurrently
            tasks = [
                self.scan_single_exchange(exchange)
                for exchange in self.apis.keys()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # Build results dictionary
            scan_results = {
                result.exchange: result
                for result in results
            }
            
            self.cache_timestamp = datetime.utcnow()
            self.logger.info("All exchange scans completed")
            
            return scan_results
            
        except Exception as e:
            self.logger.error(
                f"Error during multi-exchange scan: {str(e)}",
                exc_info=True
            )
            raise
    
    def _parse_binance_tickers(self, tickers: List[Dict[str, Any]]) -> List[TradingPair]:
        """Parse Binance ticker data into TradingPair objects."""
        pairs: List[TradingPair] = []
        
        for ticker in tickers:
            try:
                pair = TradingPair(
                    symbol=ticker.get('symbol', ''),
                    exchange="binance",
                    price=float(ticker.get('lastPrice', 0)),
                    volume_24h=float(ticker.get('volume', 0)),
                    change_24h=float(ticker.get('priceChangePercent', 0))
                )
                pairs.append(pair)
            except (ValueError, KeyError) as e:
                self.logger.debug(f"Failed to parse Binance ticker: {e}")
                continue
        
        return pairs
    
    def _parse_coinbase_products(self, products: List[Dict[str, Any]]) -> List[TradingPair]:
        """Parse Coinbase product data into TradingPair objects."""
        pairs: List[TradingPair] = []
        
        for product in products:
            try:
                # Coinbase products endpoint doesn't include price/volume
                # Skip pairs without complete data rather than using invalid 0.0 values
                # In a production system, we'd make additional API calls for stats
                self.logger.debug(
                    f"Coinbase product found: {product.get('id')} "
                    "(price/volume data requires additional API call)"
                )
                # Skip for now - would need stats API call to get valid data
                continue
            except (ValueError, KeyError) as e:
                self.logger.debug(f"Failed to parse Coinbase product: {e}")
                continue
        
        return pairs
    
    def _parse_kraken_pairs(self, data: Dict[str, Any]) -> List[TradingPair]:
        """Parse Kraken asset pairs data into TradingPair objects."""
        pairs: List[TradingPair] = []
        
        if isinstance(data, dict) and 'result' in data:
            for pair_name, pair_data in data['result'].items():
                try:
                    # Kraken asset pairs endpoint doesn't include price/volume
                    # Skip pairs without complete data rather than using invalid 0.0 values
                    # In a production system, we'd make additional API calls for ticker data
                    self.logger.debug(
                        f"Kraken pair found: {pair_name} "
                        "(price/volume data requires additional API call)"
                    )
                    # Skip for now - would need ticker API call to get valid data
                    continue
                except (ValueError, KeyError) as e:
                    self.logger.debug(f"Failed to parse Kraken pair: {e}")
                    continue
        
        return pairs
    
    def _apply_filters(self, pairs: List[TradingPair]) -> List[TradingPair]:
        """
        Apply configured filters to trading pairs.
        
        Args:
            pairs: Trading pairs to filter
            
        Returns:
            Filtered list of trading pairs
        """
        original_count = len(pairs)
        
        filtered = [
            pair for pair in pairs
            if pair.volume_24h >= self.config.min_volume
            and pair.price >= self.config.min_price
        ]
        
        self.logger.debug(
            f"Applied filters: {original_count} pairs -> {len(filtered)} pairs"
        )
        
        return filtered
    
    def export_results(
        self,
        output_format: str = "json",
        filepath: Optional[str] = None
    ) -> str:
        """
        Export scan results in specified format.
        
        Args:
            output_format: Export format ('json' or 'csv')
            filepath: File path to save results (optional)
            
        Returns:
            Exported data as string
            
        Raises:
            ValueError: If format is not supported
        """
        if output_format == "json":
            data = {
                'timestamp': self.cache_timestamp.isoformat() if self.cache_timestamp else None,
                'results': {
                    exchange: [pair.model_dump() for pair in pairs]
                    for exchange, pairs in self.scan_results.items()
                }
            }
            output = json.dumps(data, indent=2, default=str)
            
        elif output_format == "csv":
            lines = ["symbol,exchange,price,volume_24h,timestamp"]
            for pairs in self.scan_results.values():
                for pair in pairs:
                    lines.append(
                        f"{pair.symbol},{pair.exchange},{pair.price},"
                        f"{pair.volume_24h},{pair.timestamp.isoformat()}"
                    )
            output = "\n".join(lines)
            
        else:
            raise ValueError(f"Unsupported export format: {output_format}")
        
        if filepath:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            Path(filepath).write_text(output)
            self.logger.info(f"Results exported to {filepath}")
        
        return output
