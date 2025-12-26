#!/usr/bin/env python3
"""
Trade Scanner - Main entry point
Runs the trade scanner with CLI interface and comprehensive logging.
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.scanner import TradeScanner
from src.api import APIClient


def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path (default: logs/trade_scanner.log)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set default log file path
    if log_file is None:
        log_file = log_dir / "trade_scanner.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    timestamp_format = "%Y-%m-%d %H:%M:%S"
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(log_format, datefmt=timestamp_format)
    )
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter(log_format, datefmt=timestamp_format)
    )
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized - Level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {log_file}")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Trade Scanner - Monitor and scan trading opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan                 # Run scanner with default settings
  %(prog)s --scan --interval 60   # Run scanner every 60 seconds
  %(prog)s --debug                # Run with debug logging
  %(prog)s --config config.json   # Use custom configuration file
        """
    )
    
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Run the trade scanner"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start the API server"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Scan interval in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (default: logs/trade_scanner.log)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (sets log level to DEBUG)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the trade scanner application.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()
    
    # Determine log level
    log_level = logging.DEBUG if args.debug else getattr(logging, args.log_level)
    
    # Setup logging
    setup_logging(log_level=log_level, log_file=args.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Trade Scanner Application Started")
    logger.info(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info("=" * 60)
    
    try:
        # Validate configuration file
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            logger.info("Using default configuration")
        else:
            logger.info(f"Using configuration file: {config_path}")
        
        # Run scanner
        if args.scan:
            logger.info(f"Starting trade scanner (interval: {args.interval}s)")
            scanner = TradeScanner(
                config_file=args.config,
                scan_interval=args.interval
            )
            scanner.run()
        
        # Run API server
        elif args.api:
            logger.info("Starting API server")
            api_client = APIClient(config_file=args.config)
            api_client.run()
        
        # Default: run both scanner and API
        else:
            logger.info("No specific action specified. Use --scan or --api")
            logger.info("Run with --help for usage information")
            return 1
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1
    
    finally:
        logger.info("=" * 60)
        logger.info("Trade Scanner Application Stopped")
        logger.info(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        logger.info("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
