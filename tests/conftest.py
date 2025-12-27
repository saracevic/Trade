"""
PyTest Configuration and Fixtures
Provides shared fixtures and configuration for all tests.
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest

from src.models.trade import ScannerConfig, ScanResult, TradingPair


@pytest.fixture
def sample_config() -> ScannerConfig:
    """
    Provide a sample scanner configuration for testing.

    Returns:
        ScannerConfig instance with test values
    """
    return ScannerConfig(
        api_keys={"binance": "test_key", "coinbase": "test_key"},
        api_secrets={"binance": "test_secret", "coinbase": "test_secret"},
        log_level="DEBUG",
        min_volume=1000.0,
        min_price=0.01,
        enabled_exchanges=["binance", "coinbase"],
        cache_duration=300,
        timeout=10,
        retry_attempts=3,
    )


@pytest.fixture
def sample_trading_pair() -> TradingPair:
    """
    Provide a sample trading pair for testing.

    Returns:
        TradingPair instance with test data
    """
    return TradingPair(
        symbol="BTC/USDT",
        exchange="binance",
        price=45000.0,
        volume_24h=1000000.0,
        bid=44999.0,
        ask=45001.0,
        change_24h=2.5,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_trading_pairs() -> List[TradingPair]:
    """
    Provide a list of sample trading pairs for testing.

    Returns:
        List of TradingPair instances
    """
    return [
        TradingPair(
            symbol="BTC/USDT",
            exchange="binance",
            price=45000.0,
            volume_24h=1000000.0,
            change_24h=2.5,
        ),
        TradingPair(
            symbol="ETH/USDT",
            exchange="binance",
            price=2500.0,
            volume_24h=800000.0,
            change_24h=-1.2,
        ),
        TradingPair(
            symbol="BNB/USDT", exchange="binance", price=300.0, volume_24h=500000.0, change_24h=0.8
        ),
    ]


@pytest.fixture
def mock_binance_ticker() -> Dict[str, Any]:
    """
    Provide mock Binance ticker data.

    Returns:
        Dictionary with mock ticker data
    """
    return {
        "symbol": "BTCUSDT",
        "lastPrice": "45000.00",
        "volume": "1000000.00",
        "priceChangePercent": "2.5",
        "bidPrice": "44999.00",
        "askPrice": "45001.00",
    }


@pytest.fixture
def mock_binance_tickers() -> List[Dict[str, Any]]:
    """
    Provide mock Binance 24h ticker data for multiple pairs.

    Returns:
        List of ticker dictionaries
    """
    return [
        {
            "symbol": "BTCUSDT",
            "lastPrice": "45000.00",
            "volume": "1000000.00",
            "priceChangePercent": "2.5",
        },
        {
            "symbol": "ETHUSDT",
            "lastPrice": "2500.00",
            "volume": "800000.00",
            "priceChangePercent": "-1.2",
        },
        {
            "symbol": "BNBUSDT",
            "lastPrice": "300.00",
            "volume": "500000.00",
            "priceChangePercent": "0.8",
        },
    ]


@pytest.fixture
def mock_coinbase_products() -> List[Dict[str, Any]]:
    """
    Provide mock Coinbase products data.

    Returns:
        List of product dictionaries
    """
    return [
        {
            "id": "BTC-USD",
            "base_currency": "BTC",
            "quote_currency": "USD",
            "base_min_size": "0.001",
            "base_max_size": "10000",
            "status": "online",
        },
        {
            "id": "ETH-USD",
            "base_currency": "ETH",
            "quote_currency": "USD",
            "base_min_size": "0.01",
            "base_max_size": "100000",
            "status": "online",
        },
    ]


@pytest.fixture
def mock_kraken_pairs() -> Dict[str, Any]:
    """
    Provide mock Kraken asset pairs data.

    Returns:
        Dictionary with mock asset pairs
    """
    return {
        "result": {
            "XXBTZUSD": {
                "altname": "XBTUSD",
                "wsname": "XBT/USD",
                "aclass_base": "currency",
                "base": "XXBT",
                "aclass_quote": "currency",
                "quote": "ZUSD",
            },
            "XETHZUSD": {
                "altname": "ETHUSD",
                "wsname": "ETH/USD",
                "aclass_base": "currency",
                "base": "XETH",
                "aclass_quote": "currency",
                "quote": "ZUSD",
            },
        }
    }


@pytest.fixture
def sample_scan_result() -> ScanResult:
    """
    Provide a sample scan result for testing.

    Returns:
        ScanResult instance with test data
    """
    pairs = [
        TradingPair(symbol="BTC/USDT", exchange="binance", price=45000.0, volume_24h=1000000.0),
        TradingPair(symbol="ETH/USDT", exchange="binance", price=2500.0, volume_24h=800000.0),
    ]

    return ScanResult(exchange="binance", pairs=pairs, duration=1.5, success=True)


# Add markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require external services)"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
