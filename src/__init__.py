"""
Trade Scanner Package
A professional cryptocurrency trading pair scanner with multi-exchange support.
"""

__version__ = "2.0.0"
__author__ = "Trade Bot Development Team"
__description__ = "Professional multi-exchange cryptocurrency scanner"

from src.scanner.core import TradeScanner
from src.models.trade import TradingPair, ScannerConfig

__all__ = [
    "TradeScanner",
    "TradingPair",
    "ScannerConfig",
]
