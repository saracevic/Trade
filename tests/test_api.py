"""
Tests for API Modules
Tests the API classes and their functionality.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.api.base import BaseExchangeAPI
from src.api.binance import BinanceAPI
from src.api.coinbase import CoinbaseAPI
from src.api.kraken import KrakenAPI


@pytest.mark.unit
class TestBaseExchangeAPI:
    """Tests for BaseExchangeAPI abstract class."""

    def test_base_api_initialization(self):
        """Test that BaseExchangeAPI cannot be instantiated directly."""
        # BaseExchangeAPI is abstract, so we can't instantiate it directly
        # We test through a concrete implementation
        api = BinanceAPI()
        assert api.base_url == "https://fapi.binance.com"
        assert api.timeout == 20

    @patch("requests.get")
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_get.return_value = mock_response

        # Test
        api = BinanceAPI()
        result = api._make_request("/test")

        assert result == {"result": "success"}
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_make_request_retry_on_failure(self, mock_get):
        """Test that failed requests are retried."""
        # Setup mock to fail twice then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "success"}

        mock_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        # Test
        api = BinanceAPI()
        result = api._make_request("/test", retry=3)

        assert result == {"result": "success"}
        assert mock_get.call_count == 3

    @patch("requests.get")
    def test_make_request_all_retries_fail(self, mock_get):
        """Test that exception is raised after all retries fail."""
        # Setup mock to always fail
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        # Test
        api = BinanceAPI()
        with pytest.raises(requests.exceptions.RequestException):
            api._make_request("/test", retry=2)

        assert mock_get.call_count == 2


@pytest.mark.unit
class TestBinanceAPI:
    """Tests for BinanceAPI."""

    def test_binance_api_initialization(self):
        """Test Binance API initialization."""
        api = BinanceAPI()
        assert api.base_url == "https://fapi.binance.com"
        assert api.timeout == 20

    def test_binance_api_custom_timeout(self):
        """Test Binance API with custom timeout."""
        api = BinanceAPI(timeout=30)
        assert api.timeout == 30

    @patch.object(BinanceAPI, "_make_request")
    def test_get_exchange_info(self, mock_request):
        """Test getting exchange info from Binance."""
        mock_request.return_value = {"symbols": []}

        api = BinanceAPI()
        result = api.get_exchange_info()

        assert result == {"symbols": []}
        mock_request.assert_called_once_with("/fapi/v1/exchangeInfo")

    @patch.object(BinanceAPI, "_make_request")
    def test_get_ticker_24h(self, mock_request, mock_binance_tickers):
        """Test getting 24h ticker data from Binance."""
        mock_request.return_value = mock_binance_tickers

        api = BinanceAPI()
        result = api.get_ticker_24h()

        assert len(result) == 3
        assert result[0]["symbol"] == "BTCUSDT"
        mock_request.assert_called_once_with("/fapi/v1/ticker/24hr")

    @patch.object(BinanceAPI, "_make_request")
    def test_get_klines(self, mock_request):
        """Test getting kline data from Binance."""
        mock_klines = [[1609459200000, "40000", "41000", "39000", "40500", "100"]]
        mock_request.return_value = mock_klines

        api = BinanceAPI()
        result = api.get_klines("BTCUSDT", "1h")

        assert len(result) == 1
        assert result[0][0] == 1609459200000
        mock_request.assert_called_once()


@pytest.mark.unit
class TestCoinbaseAPI:
    """Tests for CoinbaseAPI."""

    def test_coinbase_api_initialization(self):
        """Test Coinbase API initialization."""
        api = CoinbaseAPI()
        assert api.base_url == "https://api.exchange.coinbase.com"
        assert api.timeout == 20

    @patch.object(CoinbaseAPI, "_make_request")
    def test_get_products(self, mock_request, mock_coinbase_products):
        """Test getting products from Coinbase."""
        mock_request.return_value = mock_coinbase_products

        api = CoinbaseAPI()
        result = api.get_products()

        assert len(result) == 2
        assert result[0]["id"] == "BTC-USD"
        mock_request.assert_called_once_with("/products")

    @patch.object(CoinbaseAPI, "_make_request")
    def test_get_product_stats(self, mock_request):
        """Test getting product stats from Coinbase."""
        mock_stats = {"open": "40000", "high": "41000", "low": "39000", "last": "40500"}
        mock_request.return_value = mock_stats

        api = CoinbaseAPI()
        result = api.get_product_stats("BTC-USD")

        assert result["last"] == "40500"
        mock_request.assert_called_once_with("/products/BTC-USD/stats")


@pytest.mark.unit
class TestKrakenAPI:
    """Tests for KrakenAPI."""

    def test_kraken_api_initialization(self):
        """Test Kraken API initialization."""
        api = KrakenAPI()
        assert api.base_url == "https://api.kraken.com"
        assert api.timeout == 20

    @patch.object(KrakenAPI, "_make_request")
    def test_get_asset_pairs(self, mock_request, mock_kraken_pairs):
        """Test getting asset pairs from Kraken."""
        mock_request.return_value = mock_kraken_pairs

        api = KrakenAPI()
        result = api.get_asset_pairs()

        assert "result" in result
        assert "XXBTZUSD" in result["result"]
        mock_request.assert_called_once_with("/0/public/AssetPairs")

    @patch.object(KrakenAPI, "_make_request")
    def test_get_ohlc(self, mock_request):
        """Test getting OHLC data from Kraken."""
        mock_ohlc = {
            "result": {
                "XXBTZUSD": [[1609459200, "40000", "41000", "39000", "40500", "40250", "100", 50]],
                "last": 1609459200,
            }
        }
        mock_request.return_value = mock_ohlc

        api = KrakenAPI()
        result = api.get_ohlc("XXBTZUSD", interval=60)

        assert len(result) == 1
        assert result[0][0] == 1609459200
