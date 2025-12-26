"""
Trade Data Models
Pydantic models for data validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class ExchangeType(str, Enum):
    """Enumeration of supported cryptocurrency exchanges."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    COINGECKO = "coingecko"


class TradingPair(BaseModel):
    """
    Represents a trading pair from an exchange.
    
    This model validates and serializes trading pair data with
    proper type checking and default values.
    
    Attributes:
        symbol: Trading pair symbol (e.g., 'BTC/USD')
        exchange: Exchange name
        price: Current price
        volume_24h: 24-hour trading volume
        bid: Current bid price (optional)
        ask: Current ask price (optional)
        change_24h: 24-hour price change percentage (optional)
        timestamp: When this data was captured
    """
    
    symbol: str = Field(..., description="Trading pair symbol")
    exchange: str = Field(..., description="Exchange name")
    price: float = Field(..., gt=0, description="Current price")
    volume_24h: float = Field(..., ge=0, description="24-hour volume")
    bid: Optional[float] = Field(None, gt=0, description="Bid price")
    ask: Optional[float] = Field(None, gt=0, description="Ask price")
    change_24h: Optional[float] = Field(None, description="24h change %")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trading pair to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the trading pair
        """
        data = self.model_dump()
        # Convert datetime to ISO format string
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data
    
    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat()
        },
        'use_enum_values': True
    }


class ScannerConfig(BaseModel):
    """
    Configuration model for the trade scanner.
    
    Uses Pydantic for validation and environment variable loading.
    
    Attributes:
        api_keys: API keys for each exchange
        api_secrets: API secrets for each exchange
        log_level: Logging level
        log_file: Path to log file
        min_volume: Minimum trading volume filter
        min_price: Minimum price filter
        cache_duration: Cache duration in seconds
        timeout: API request timeout
        retry_attempts: Number of retry attempts
        enabled_exchanges: List of enabled exchanges
        output_dir: Directory for output files
    """
    
    api_keys: Dict[str, str] = Field(default_factory=dict)
    api_secrets: Dict[str, str] = Field(default_factory=dict)
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default=None)
    min_volume: float = Field(default=1000.0, ge=0)
    min_price: float = Field(default=0.00001, gt=0)
    cache_duration: int = Field(default=300, ge=0)
    timeout: int = Field(default=10, gt=0)
    retry_attempts: int = Field(default=3, ge=1)
    enabled_exchanges: List[str] = Field(
        default_factory=lambda: [e.value for e in ExchangeType]
    )
    output_dir: str = Field(default="out")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator('enabled_exchanges')
    @classmethod
    def validate_exchanges(cls, v: List[str]) -> List[str]:
        """Validate enabled exchanges are supported."""
        valid_exchanges = [e.value for e in ExchangeType]
        for exchange in v:
            if exchange not in valid_exchanges:
                raise ValueError(
                    f"Exchange '{exchange}' not supported. "
                    f"Must be one of {valid_exchanges}"
                )
        return v
    
    @classmethod
    def from_json(cls, json_path: str) -> "ScannerConfig":
        """
        Load configuration from a JSON file.
        
        Args:
            json_path: Path to JSON configuration file
            
        Returns:
            ScannerConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        import json
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def to_json(self, json_path: str) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            json_path: Path where to save JSON configuration
        """
        import json
        
        # Create directory if it doesn't exist
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
    
    model_config = {
        'use_enum_values': True
    }


class ScanResult(BaseModel):
    """
    Model for scan results.
    
    Attributes:
        timestamp: When the scan was performed
        exchange: Exchange name
        pairs: List of trading pairs found
        duration: Scan duration in seconds
        success: Whether scan was successful
        error: Error message if scan failed
    """
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    exchange: str = Field(..., description="Exchange name")
    pairs: List[TradingPair] = Field(default_factory=list)
    duration: float = Field(..., ge=0, description="Scan duration in seconds")
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)
    
    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat()
        }
    }
