"""
Application Settings Module
Pydantic-based configuration management with environment variable support.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Settings can be loaded from environment variables or .env file.
    Environment variables take precedence over .env file values.
    
    Usage:
        settings = Settings()
        print(settings.app_name)
    """
    
    # Application Settings
    app_name: str = Field(default="Trade Scanner", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="production", description="Environment (development/production/testing)")
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "logs")
    output_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "out")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    api_workers: int = Field(default=4, ge=1, description="Number of API workers")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Security Settings
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for encryption"
    )
    algorithm: str = Field(default="HS256", description="Encryption algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiration in minutes"
    )
    
    # Cache Settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_timeout: int = Field(default=3600, ge=0, description="Cache timeout in seconds")
    
    # Trading Settings
    max_retries: int = Field(default=3, ge=1, description="Maximum retry attempts")
    request_timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(
        default=60,
        ge=1,
        description="Rate limit requests per minute"
    )
    
    # Scanner Settings
    min_volume: float = Field(default=1000.0, ge=0, description="Minimum trading volume")
    min_price: float = Field(default=0.00001, gt=0, description="Minimum price")
    enabled_exchanges: List[str] = Field(
        default_factory=lambda: ["binance", "coinbase", "kraken"],
        description="Enabled exchanges"
    )
    
    # API Keys (should be set via environment variables)
    binance_api_key: str = Field(default="", description="Binance API key")
    binance_api_secret: str = Field(default="", description="Binance API secret")
    coinbase_api_key: str = Field(default="", description="Coinbase API key")
    coinbase_api_secret: str = Field(default="", description="Coinbase API secret")
    kraken_api_key: str = Field(default="", description="Kraken API key")
    kraken_api_secret: str = Field(default="", description="Kraken API secret")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_api_keys(self) -> Dict[str, str]:
        """
        Get API keys as a dictionary.
        
        Returns:
            Dictionary mapping exchange names to API keys
        """
        return {
            "binance": self.binance_api_key,
            "coinbase": self.coinbase_api_key,
            "kraken": self.kraken_api_key,
        }
    
    def get_api_secrets(self) -> Dict[str, str]:
        """
        Get API secrets as a dictionary.
        
        Returns:
            Dictionary mapping exchange names to API secrets
        """
        return {
            "binance": self.binance_api_secret,
            "coinbase": self.coinbase_api_secret,
            "kraken": self.kraken_api_secret,
        }
    
    def validate(self) -> bool:
        """
        Validate settings for production environment.
        
        Returns:
            True if settings are valid
            
        Raises:
            ValueError: If critical settings are invalid
        """
        if self.environment == "production":
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed in production")
            
            if self.debug:
                raise ValueError("DEBUG must be False in production")
        
        return True
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.data_dir, self.logs_dir, self.output_dir]:
            directory.mkdir(parents=True, exist_ok=True)


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings


class DevelopmentSettings(Settings):
    """Development environment settings."""
    
    debug: bool = True
    environment: str = "development"
    log_level: str = "DEBUG"
    cache_enabled: bool = False


class TestingSettings(Settings):
    """Testing environment settings."""
    
    environment: str = "testing"
    log_level: str = "DEBUG"
    cache_enabled: bool = False
    rate_limit_enabled: bool = False


class ProductionSettings(Settings):
    """Production environment settings."""
    
    debug: bool = False
    environment: str = "production"
    log_level: str = "WARNING"


def get_settings_for_env(env: Optional[str] = None) -> Settings:
    """
    Get settings for specific environment.
    
    Args:
        env: Environment name (development/testing/production)
            If None, uses APP_ENV environment variable or defaults to production
    
    Returns:
        Settings instance for the specified environment
    """
    if env is None:
        env = os.getenv("APP_ENV", "production").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "testing": TestingSettings,
        "production": ProductionSettings,
    }
    
    settings_class = settings_map.get(env, ProductionSettings)
    return settings_class()
