"""
Core Scanner Module
Main trade scanner implementation with multi-exchange support.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.api.binance import BinanceAPI
from src.api.coinbase import CoinbaseAPI
from src.api.kraken import KrakenAPI
from src.models.trade import ScannerConfig, ScanResult, TradingPair
from src.utils.logger import LoggerMixin, setup_logger

# Rate limiting configuration
API_RATE_LIMIT_DELAY = 0.15  # Seconds between API calls


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

    async def scan_single_exchange(self, exchange: str) -> ScanResult:
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
                pairs = await self._parse_coinbase_products(products)
            elif exchange == "kraken":
                asset_pairs = await asyncio.to_thread(api.get_asset_pairs)
                pairs = await self._parse_kraken_pairs(asset_pairs)
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
                exchange=exchange, pairs=filtered_pairs, duration=duration, success=True
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"Error scanning {exchange}: {str(e)}", exc_info=True)

            return ScanResult(
                exchange=exchange, pairs=[], duration=duration, success=False, error=str(e)
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
                exchange: ScanResult(exchange=exchange, pairs=pairs, duration=0.0, success=True)
                for exchange, pairs in self.scan_results.items()
            }

        try:
            # Scan all exchanges concurrently
            tasks = [self.scan_single_exchange(exchange) for exchange in self.apis.keys()]

            results = await asyncio.gather(*tasks, return_exceptions=False)

            # Build results dictionary
            scan_results = {result.exchange: result for result in results}

            self.cache_timestamp = datetime.utcnow()
            self.logger.info("All exchange scans completed")

            return scan_results

        except Exception as e:
            self.logger.error(f"Error during multi-exchange scan: {str(e)}", exc_info=True)
            raise

    def _parse_binance_tickers(self, tickers: List[Dict[str, Any]]) -> List[TradingPair]:
        """Parse Binance ticker data into TradingPair objects."""
        pairs: List[TradingPair] = []

        for ticker in tickers:
            try:
                pair = TradingPair(
                    symbol=ticker.get("symbol", ""),
                    exchange="binance",
                    price=float(ticker.get("lastPrice", 0)),
                    volume_24h=float(ticker.get("volume", 0)),
                    change_24h=float(ticker.get("priceChangePercent", 0)),
                )
                pairs.append(pair)
            except (ValueError, KeyError) as e:
                self.logger.debug(f"Failed to parse Binance ticker: {e}")
                continue

        return pairs

    async def _parse_coinbase_products(self, products: List[Dict[str, Any]]) -> List[TradingPair]:
        """Parse Coinbase product data into TradingPair objects."""
        pairs: List[TradingPair] = []

        # Filter for perpetual/spot products and limit to 100
        perpetual_products = []
        for product in products:
            product_id = product.get("id", "")
            # Filter for trading pairs (typically contain '-')
            # Avoid test/disabled products
            if "-" in product_id and product.get("status") == "online":
                perpetual_products.append(product)

        # Limit to first 100 products
        perpetual_products = perpetual_products[:100]

        self.logger.info(f"Fetching stats for {len(perpetual_products)} Coinbase products...")

        # Fetch stats for each product with rate limiting
        api = self.apis.get("coinbase")

        for i, product in enumerate(perpetual_products):
            product_id = product.get("id", "")
            try:
                # Add rate limiting
                if i > 0:
                    await asyncio.sleep(API_RATE_LIMIT_DELAY)

                self.logger.debug(f"Fetching stats for Coinbase product: {product_id}")
                stats = await asyncio.to_thread(api.get_product_stats, product_id)

                if not stats:
                    self.logger.debug(f"No stats available for {product_id}")
                    continue

                # Parse stats data with proper validation
                last_price_str = stats.get("last", "0")
                volume_str = stats.get("volume", "0")

                try:
                    price = float(last_price_str) if last_price_str else 0.0
                    volume = float(volume_str) if volume_str else 0.0
                except (ValueError, TypeError) as e:
                    self.logger.debug(f"Invalid price/volume data for {product_id}: {e}")
                    continue

                if price > 0 and volume > 0:
                    pair = TradingPair(
                        symbol=product_id,
                        exchange="coinbase",
                        price=price,
                        volume_24h=volume,
                        change_24h=None,  # Coinbase doesn't provide this in stats
                    )
                    pairs.append(pair)
                    self.logger.debug(
                        f"Added Coinbase pair: {product_id} (price: {price}, volume: {volume})"
                    )

            except Exception as e:
                self.logger.warning(f"Failed to fetch stats for Coinbase product {product_id}: {e}")
                continue

        self.logger.info(
            f"Successfully parsed {len(pairs)} Coinbase products with price/volume data"
        )
        return pairs

    async def _parse_kraken_pairs(self, data: Dict[str, Any]) -> List[TradingPair]:
        """Parse Kraken asset pairs data into TradingPair objects."""
        pairs: List[TradingPair] = []

        if not isinstance(data, dict) or "result" not in data:
            self.logger.warning("Invalid Kraken asset pairs data format")
            return pairs

        # Get list of trading pairs
        asset_pairs_data = data["result"]
        pair_names = list(asset_pairs_data.keys())

        # Filter for perpetual/spot pairs (exclude .d suffix which are dark pool)
        perpetual_pairs = [pair for pair in pair_names if not pair.endswith(".d")]

        # Limit to first 100 pairs
        perpetual_pairs = perpetual_pairs[:100]

        self.logger.info(f"Fetching ticker data for {len(perpetual_pairs)} Kraken pairs...")

        # Fetch ticker data in batches (Kraken allows multiple pairs in one request)
        # But we'll batch them to avoid hitting request limits
        api = self.apis.get("kraken")

        batch_size = 10  # Process 10 pairs per request to avoid URL length issues
        for i in range(0, len(perpetual_pairs), batch_size):
            batch = perpetual_pairs[i : i + batch_size]
            pair_list = ",".join(batch)

            try:
                # Add rate limiting between batches
                if i > 0:
                    await asyncio.sleep(API_RATE_LIMIT_DELAY)

                self.logger.debug(f"Fetching ticker for Kraken pairs: {pair_list}")
                ticker_data = await asyncio.to_thread(api.get_ticker, pair_list)

                if not isinstance(ticker_data, dict) or "result" not in ticker_data:
                    self.logger.warning(f"Invalid ticker data for batch: {pair_list}")
                    continue

                # Parse ticker data for each pair
                for pair_name, ticker_info in ticker_data["result"].items():
                    try:
                        # Kraken ticker format: {'a': [ask_price, ...], 'b': [bid_price, ...],
                        #                        'c': [last_price, ...], 'v': [volume_today, volume_24h], ...}
                        last_price = ticker_info.get("c", [0, 0])
                        volume_data = ticker_info.get("v", [0, 0])

                        # Safely extract and convert price and volume
                        price = 0.0
                        volume = 0.0

                        if isinstance(last_price, list) and len(last_price) > 0:
                            try:
                                price = float(last_price[0])
                            except (ValueError, TypeError):
                                pass

                        if isinstance(volume_data, list) and len(volume_data) > 1:
                            try:
                                volume = float(volume_data[1])
                            except (ValueError, TypeError):
                                pass

                        if price > 0 and volume > 0:
                            pair = TradingPair(
                                symbol=pair_name,
                                exchange="kraken",
                                price=price,
                                volume_24h=volume,
                                change_24h=None,  # Kraken doesn't provide 24h change directly
                            )
                            pairs.append(pair)
                            self.logger.debug(
                                f"Added Kraken pair: {pair_name} (price: {price}, volume: {volume})"
                            )

                    except (ValueError, KeyError, IndexError) as e:
                        self.logger.debug(f"Failed to parse Kraken ticker for {pair_name}: {e}")
                        continue

            except Exception as e:
                self.logger.warning(f"Failed to fetch ticker for Kraken batch {pair_list}: {e}")
                continue

        self.logger.info(f"Successfully parsed {len(pairs)} Kraken pairs with price/volume data")
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
            pair
            for pair in pairs
            if pair.volume_24h >= self.config.min_volume and pair.price >= self.config.min_price
        ]

        self.logger.debug(f"Applied filters: {original_count} pairs -> {len(filtered)} pairs")

        return filtered

    def export_results(self, output_format: str = "json", filepath: Optional[str] = None) -> str:
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
                "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None,
                "results": {
                    exchange: [pair.model_dump() for pair in pairs]
                    for exchange, pairs in self.scan_results.items()
                },
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
