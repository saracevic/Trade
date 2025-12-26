"""
Main Entry Point
Trade Scanner Application - Professional multi-exchange cryptocurrency scanner.
"""

import asyncio
import argparse
import sys
from pathlib import Path

from src.models.trade import ScannerConfig
from src.scanner.core import TradeScanner
from src.utils.logger import setup_logger
from config.settings import get_settings


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Trade Scanner - Multi-exchange cryptocurrency scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Run with default settings
  python main.py --exchanges binance      # Scan only Binance
  python main.py --min-volume 10000       # Set minimum volume filter
  python main.py --output results.json    # Save to custom file
  python main.py --config custom.json     # Load custom configuration
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file'
    )
    
    parser.add_argument(
        '--exchanges',
        nargs='+',
        choices=['binance', 'coinbase', 'kraken'],
        help='Exchanges to scan (space-separated)'
    )
    
    parser.add_argument(
        '--min-volume',
        type=float,
        help='Minimum 24h trading volume filter'
    )
    
    parser.add_argument(
        '--min-price',
        type=float,
        help='Minimum price filter'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='out/results.json',
        help='Output file path (default: out/results.json)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable result caching'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'csv'],
        default='json',
        help='Output format (default: json)'
    )
    
    return parser.parse_args()


def create_config(args: argparse.Namespace) -> ScannerConfig:
    """
    Create scanner configuration from arguments and settings.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        ScannerConfig instance
    """
    # Load settings
    settings = get_settings()
    
    # If config file specified, load it
    if args.config:
        config = ScannerConfig.from_json(args.config)
    else:
        # Create config from settings and arguments
        config = ScannerConfig(
            api_keys=settings.get_api_keys(),
            api_secrets=settings.get_api_secrets(),
            log_level=args.log_level,
            min_volume=args.min_volume if args.min_volume is not None else settings.min_volume,
            min_price=args.min_price if args.min_price is not None else settings.min_price,
            enabled_exchanges=args.exchanges if args.exchanges else settings.enabled_exchanges,
            cache_duration=0 if args.no_cache else 300,
            timeout=settings.request_timeout,
            retry_attempts=settings.max_retries,
            output_dir=str(settings.output_dir)
        )
    
    return config


async def main_async(args: argparse.Namespace) -> int:
    """
    Async main function.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger = setup_logger(__name__, level=args.log_level)
    
    try:
        # Create configuration
        config = create_config(args)
        
        logger.info("=" * 70)
        logger.info("Trade Scanner v2.0.0 - Starting")
        logger.info("=" * 70)
        logger.info(f"Enabled exchanges: {', '.join(config.enabled_exchanges)}")
        logger.info(f"Min volume: {config.min_volume}")
        logger.info(f"Min price: {config.min_price}")
        logger.info(f"Output: {args.output}")
        logger.info("=" * 70)
        
        # Initialize scanner
        scanner = TradeScanner(config)
        
        # Run scan
        logger.info("Starting scan...")
        results = await scanner.scan_all_exchanges()
        
        # Display results summary
        logger.info("=" * 70)
        logger.info("Scan Results Summary:")
        logger.info("=" * 70)
        
        total_pairs = 0
        for exchange, result in results.items():
            status = "✓" if result.success else "✗"
            pairs_count = len(result.pairs)
            total_pairs += pairs_count
            
            logger.info(
                f"{status} {exchange:12} | "
                f"{pairs_count:5} pairs | "
                f"{result.duration:6.2f}s"
            )
            
            if not result.success and result.error:
                logger.error(f"  Error: {result.error}")
        
        logger.info("=" * 70)
        logger.info(f"Total pairs found: {total_pairs}")
        logger.info("=" * 70)
        
        # Export results
        logger.info(f"Exporting results to {args.output}...")
        scanner.export_results(
            output_format=args.format,
            filepath=args.output
        )
        
        logger.info("Scan completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    args = parse_arguments()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
