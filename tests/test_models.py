"""
Tests for Data Models
Tests Pydantic models for validation and serialization.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.trade import TradingPair, ScannerConfig, ScanResult, ExchangeType


@pytest.mark.unit
class TestTradingPair:
    """Tests for TradingPair model."""
    
    def test_create_valid_trading_pair(self):
        """Test creating a valid trading pair."""
        pair = TradingPair(
            symbol="BTC/USDT",
            exchange="binance",
            price=45000.0,
            volume_24h=1000000.0
        )
        
        assert pair.symbol == "BTC/USDT"
        assert pair.exchange == "binance"
        assert pair.price == 45000.0
        assert pair.volume_24h == 1000000.0
        assert isinstance(pair.timestamp, datetime)
    
    def test_trading_pair_with_optional_fields(self):
        """Test trading pair with all optional fields."""
        pair = TradingPair(
            symbol="ETH/USDT",
            exchange="coinbase",
            price=2500.0,
            volume_24h=800000.0,
            bid=2499.0,
            ask=2501.0,
            change_24h=1.5
        )
        
        assert pair.bid == 2499.0
        assert pair.ask == 2501.0
        assert pair.change_24h == 1.5
    
    def test_trading_pair_invalid_price(self):
        """Test that negative price raises validation error."""
        with pytest.raises(ValidationError):
            TradingPair(
                symbol="BTC/USDT",
                exchange="binance",
                price=-100.0,
                volume_24h=1000000.0
            )
    
    def test_trading_pair_invalid_volume(self):
        """Test that negative volume raises validation error."""
        with pytest.raises(ValidationError):
            TradingPair(
                symbol="BTC/USDT",
                exchange="binance",
                price=45000.0,
                volume_24h=-1000.0
            )
    
    def test_trading_pair_to_dict(self, sample_trading_pair):
        """Test converting trading pair to dictionary."""
        pair_dict = sample_trading_pair.to_dict()
        
        assert isinstance(pair_dict, dict)
        assert pair_dict['symbol'] == "BTC/USDT"
        assert pair_dict['exchange'] == "binance"
        assert pair_dict['price'] == 45000.0
        assert 'timestamp' in pair_dict


@pytest.mark.unit
class TestScannerConfig:
    """Tests for ScannerConfig model."""
    
    def test_create_valid_config(self):
        """Test creating a valid scanner configuration."""
        config = ScannerConfig(
            api_keys={"binance": "key1"},
            api_secrets={"binance": "secret1"},
            log_level="INFO",
            min_volume=1000.0,
            min_price=0.01
        )
        
        assert config.log_level == "INFO"
        assert config.min_volume == 1000.0
        assert config.min_price == 0.01
        assert "binance" in config.enabled_exchanges
    
    def test_config_with_defaults(self):
        """Test configuration with default values."""
        config = ScannerConfig(
            api_keys={},
            api_secrets={}
        )
        
        assert config.log_level == "INFO"
        assert config.cache_duration == 300
        assert config.timeout == 10
        assert config.retry_attempts == 3
        assert len(config.enabled_exchanges) > 0
    
    def test_config_invalid_log_level(self):
        """Test that invalid log level raises validation error."""
        with pytest.raises(ValidationError):
            ScannerConfig(
                api_keys={},
                api_secrets={},
                log_level="INVALID"
            )
    
    def test_config_invalid_min_volume(self):
        """Test that negative min_volume raises validation error."""
        with pytest.raises(ValidationError):
            ScannerConfig(
                api_keys={},
                api_secrets={},
                min_volume=-100.0
            )
    
    def test_config_invalid_min_price(self):
        """Test that zero or negative min_price raises validation error."""
        with pytest.raises(ValidationError):
            ScannerConfig(
                api_keys={},
                api_secrets={},
                min_price=0.0
            )
    
    def test_config_invalid_exchange(self):
        """Test that invalid exchange raises validation error."""
        with pytest.raises(ValidationError):
            ScannerConfig(
                api_keys={},
                api_secrets={},
                enabled_exchanges=["invalid_exchange"]
            )


@pytest.mark.unit
class TestScanResult:
    """Tests for ScanResult model."""
    
    def test_create_successful_scan_result(self, sample_trading_pairs):
        """Test creating a successful scan result."""
        result = ScanResult(
            exchange="binance",
            pairs=sample_trading_pairs,
            duration=1.5,
            success=True
        )
        
        assert result.exchange == "binance"
        assert len(result.pairs) == 3
        assert result.duration == 1.5
        assert result.success is True
        assert result.error is None
    
    def test_create_failed_scan_result(self):
        """Test creating a failed scan result."""
        result = ScanResult(
            exchange="binance",
            pairs=[],
            duration=0.5,
            success=False,
            error="Connection timeout"
        )
        
        assert result.success is False
        assert result.error == "Connection timeout"
        assert len(result.pairs) == 0
    
    def test_scan_result_negative_duration(self):
        """Test that negative duration raises validation error."""
        with pytest.raises(ValidationError):
            ScanResult(
                exchange="binance",
                pairs=[],
                duration=-1.0,
                success=True
            )


@pytest.mark.unit
class TestExchangeType:
    """Tests for ExchangeType enum."""
    
    def test_exchange_type_values(self):
        """Test that all exchange types have correct values."""
        assert ExchangeType.BINANCE.value == "binance"
        assert ExchangeType.COINBASE.value == "coinbase"
        assert ExchangeType.KRAKEN.value == "kraken"
        assert ExchangeType.COINGECKO.value == "coingecko"
    
    def test_exchange_type_iteration(self):
        """Test iterating over exchange types."""
        exchanges = [e.value for e in ExchangeType]
        assert "binance" in exchanges
        assert "coinbase" in exchanges
        assert "kraken" in exchanges
        assert "coingecko" in exchanges
