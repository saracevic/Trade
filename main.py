#!/usr/bin/env python3

import asyncio
import json
import logging

from src.models.trade import ScannerConfig
from src.scanner.core import TradeScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the scanner."""
    try:
        logger.info("Starting Trade Scanner...")

        # Initialize configuration with defaults
        config = ScannerConfig()

        # Initialize the scanner
        scanner = TradeScanner(config)

        # Run the scan
        scan_results = await scanner.scan_all_exchanges()

        # Convert results to JSON-serializable format
        # Extract timestamp from first available result
        timestamp = None
        if scan_results:
            for exchange_name in scan_results:
                if scan_results[exchange_name].pairs:
                    timestamp = scan_results[exchange_name].pairs[0].timestamp.isoformat()
                    break

        # Use current time if no timestamp found
        from datetime import datetime, timezone

        generated_at = timestamp or datetime.now(timezone.utc).isoformat()

        results = {
            "timestamp": timestamp,
            "generated_at": generated_at,
            "exchanges": {},
            "results": [],  # For compatibility with HTML
        }

        for exchange, result in scan_results.items():
            results["exchanges"][exchange] = [pair.to_dict() for pair in result.pairs]

        # Export results to JSON
        with open("results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Scan complete. Results written to results.json")
        logger.info(f"Total exchanges scanned: {len(results.get('exchanges', {}))}")
        for exchange, pairs in results.get("exchanges", {}).items():
            logger.info(f"  {exchange}: {len(pairs)} pairs")

    except Exception as e:
        logger.error(f"Error running scanner: {e}", exc_info=True)
        # Create results.json with error message even on failure
        from datetime import datetime, timezone

        error_results = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": None,
            "error": str(e),
            "exchanges": {},
            "results": [],
        }
        with open("results.json", "w") as f:
            json.dump(error_results, f, indent=2)
        logger.error("Created results.json with error information")
        raise


if __name__ == "__main__":
    asyncio.run(main())
