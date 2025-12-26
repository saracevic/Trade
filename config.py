"""
Configuration Management Module
Handles all configuration settings for the Trade application.
Created: 2025-12-26 16:02:41 UTC
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """Base configuration class with common settings."""
    
    # Application settings
    APP_NAME = "Trade"
    APP_VERSION = "1.0.0"
    DEBUG = False
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trade.db")
    DATABASE_ECHO = False
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_WORKERS = int(os.getenv("API_WORKERS", 4))
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Cache settings
    CACHE_ENABLED = True
    CACHE_TIMEOUT = 3600  # 1 hour
    
    # Trading settings
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and key.isupper()
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        required_settings = ["SECRET_KEY", "DATABASE_URL"]
        for setting in required_settings:
            if not getattr(cls, setting, None):
                raise ValueError(f"Missing required setting: {setting}")
        return True


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    DATABASE_URL = os.getenv("DEV_DATABASE_URL", "sqlite:///dev_trade.db")
    DATABASE_ECHO = True
    LOG_LEVEL = "DEBUG"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    CACHE_ENABLED = False


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    DATABASE_ECHO = False
    LOG_LEVEL = "DEBUG"
    SECRET_KEY = "test-secret-key"
    CACHE_ENABLED = False
    RATE_LIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    DATABASE_ECHO = False
    LOG_LEVEL = "WARNING"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate production configuration."""
        super().validate()
        
        # Ensure SECRET_KEY is not default
        if cls.SECRET_KEY == Config.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")
        
        # Ensure DATABASE_URL is set
        if "sqlite" in cls.DATABASE_URL.lower():
            raise ValueError("SQLite is not recommended for production")
        
        return True


# Configuration factory
def get_config(env: str = None) -> Config:
    """
    Get configuration object based on environment.
    
    Args:
        env: Environment name (development, testing, production)
        
    Returns:
        Configuration object
    """
    if env is None:
        env = os.getenv("APP_ENV", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()


# Default configuration
config = get_config()
