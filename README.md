# Trade Scanner 🚀

[![Tests](https://github.com/saracevic/Trade/actions/workflows/tests.yml/badge.svg)](https://github.com/saracevic/Trade/actions/workflows/tests.yml)
[![Lint](https://github.com/saracevic/Trade/actions/workflows/lint.yml/badge.svg)](https://github.com/saracevic/Trade/actions/workflows/lint.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Professional multi-exchange cryptocurrency trading pair scanner with industrial-grade architecture, comprehensive testing, and production-ready deployment options.

## 🎯 Overview

Trade Scanner is a sophisticated cryptocurrency market analysis tool that monitors multiple exchanges for specific trading signals:

- **Friday Asian-range 50% midline** (script's `midline_body`) touch after session end
- **50% Fibonacci** (from ATH/ATL via daily candles) touches after session end

The scanner aggregates results from multiple exchanges and publishes them to a professional web interface at [https://saracevic.github.io/Trade/](https://saracevic.github.io/Trade/).

## ✨ Features

- 🔄 **Multi-Exchange Support**: Scan Binance Futures, Coinbase, and Kraken simultaneously
- 🎯 **Advanced Filtering**: Filter by volume, price, and custom technical criteria
- 📊 **Real-time Data**: Fetch live market data from multiple exchanges
- 🌐 **Web Interface**: Professional, responsive UI with real-time updates
- 🐳 **Docker Ready**: Production-ready containerization with docker-compose
- ✅ **Comprehensive Testing**: 31+ unit tests with 40% coverage
- 📝 **Professional Logging**: Structured logging with multiple levels
- ⚙️ **Flexible Configuration**: Environment variables, JSON, or CLI arguments
- 🔒 **Type Safe**: Full type hints with Pydantic validation
- 📈 **Export Options**: JSON and CSV output formats
- 🔧 **Developer Friendly**: Pre-commit hooks, linting, and formatting tools
- 🚀 **CI/CD Ready**: Automated testing, linting, and deployment workflows

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/saracevic/Trade.git
cd Trade

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python main.py
```

### Docker Installation

```bash
# Build and run with Docker
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📖 Usage

### Command Line Interface

```bash
# Basic usage (scans all enabled exchanges)
python main.py

# Scan specific exchanges
python main.py --exchanges binance coinbase

# Apply filters
python main.py --min-volume 100000 --min-price 0.01

# Custom output
python main.py --output my_results.json --format json

# Debug mode
python main.py --log-level DEBUG

# Legacy scanner (for backward compatibility)
python scanner.py
```

### Python API

```python
import asyncio
from src.scanner.core import TradeScanner
from src.models.trade import ScannerConfig

# Create configuration
config = ScannerConfig(
    api_keys={"binance": "your_key"},
    api_secrets={"binance": "your_secret"},
    enabled_exchanges=["binance", "coinbase"],
    min_volume=10000.0,
    min_price=0.01
)

# Initialize scanner
scanner = TradeScanner(config)

# Run scan
async def main():
    results = await scanner.scan_all_exchanges()
    for exchange, result in results.items():
        print(f"{exchange}: {len(result.pairs)} pairs found")

asyncio.run(main())
```

### GitHub Actions Automation

The project includes automated workflows:

- **Daily Scan**: Runs automatically via `.github/workflows/scan.yml`
- **Manual Scan**: Trigger from Actions tab or the web interface
- **Results Publishing**: Automatically publishes to GitHub Pages

## 📁 Project Structure

```
Trade/
├── src/                          # Source code (modular architecture)
│   ├── api/                      # Exchange API clients
│   │   ├── base.py              # Abstract base class
│   │   ├── binance.py           # Binance Futures implementation
│   │   ├── coinbase.py          # Coinbase Exchange implementation
│   │   ├── kraken.py            # Kraken implementation
│   │   └── coingecko.py         # CoinGecko implementation
│   ├── scanner/                  # Scanner logic
│   │   └── core.py              # Main scanner implementation
│   ├── models/                   # Data models
│   │   └── trade.py             # Pydantic models
│   └── utils/                    # Utilities
│       └── logger.py            # Logging setup
├── config/                       # Configuration
│   └── settings.py              # Pydantic settings
├── tests/                        # Test suite
│   ├── conftest.py              # Test fixtures
│   ├── test_api.py              # API tests
│   └── test_models.py           # Model tests
├── .github/workflows/            # CI/CD workflows
│   ├── tests.yml                # Test automation
│   ├── lint.yml                 # Code quality checks
│   ├── scan.yml                 # Daily scanner
│   └── manual_scan.yml          # Manual trigger
├── index.html                    # Web interface
├── main.py                       # Modern CLI entry point
├── scanner.py                    # Legacy scanner (backward compat)
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker orchestration
├── pyproject.toml               # Project configuration
├── requirements.txt             # Production dependencies
└── requirements-dev.txt         # Development dependencies
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application
APP_NAME=Trade Scanner
ENVIRONMENT=production
DEBUG=false

# API Keys (optional for public endpoints)
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
COINBASE_API_KEY=your_coinbase_key
COINBASE_API_SECRET=your_coinbase_secret

# Scanner Settings
MIN_VOLUME=1000.0
MIN_PRICE=0.00001
ENABLED_EXCHANGES=binance,coinbase,kraken

# Logging
LOG_LEVEL=INFO
```

### JSON Configuration

Create a custom configuration file:

```json
{
  "api_keys": {
    "binance": "your_key",
    "coinbase": "your_key"
  },
  "api_secrets": {
    "binance": "your_secret",
    "coinbase": "your_secret"
  },
  "enabled_exchanges": ["binance", "coinbase"],
  "min_volume": 10000.0,
  "min_price": 0.01,
  "log_level": "INFO"
}
```

Load it with: `python main.py --config my_config.json`

## 🧪 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run linters
black src/ tests/ main.py
isort src/ tests/ main.py
flake8 src/ tests/ main.py
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run only unit tests
pytest -m unit
```

### Code Quality Tools

The project uses several tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **Flake8**: Linting and style checking
- **mypy**: Static type checking
- **pre-commit**: Automated pre-commit hooks
- **pytest**: Testing framework with asyncio support

## 📊 CI/CD

The project includes GitHub Actions workflows for:

- **Tests**: Automated testing on Python 3.9, 3.10, and 3.11
- **Lint**: Code quality checks with Black, Flake8, isort, and mypy
- **Coverage**: Automated coverage reports uploaded to Codecov
- **Daily Scans**: Automated market scanning and results publishing
- **Manual Scans**: On-demand scanning via workflow dispatch

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t trade-scanner .

# Run container
docker run -d --name scanner \
  -e BINANCE_API_KEY=your_key \
  -e BINANCE_API_SECRET=your_secret \
  -v $(pwd)/out:/app/out \
  trade-scanner
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f scanner

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

## 🌐 Web Interface

The project includes a professional web interface (`index.html`) with:

- **Real-time Updates**: Auto-refresh from results.json
- **Advanced Filtering**: Search and filter by exchange, symbol, and signals
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Professional design with smooth animations
- **Multi-language Support**: Turkish interface with English fallback

Access the live interface at: [https://saracevic.github.io/Trade/](https://saracevic.github.io/Trade/)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks (`pre-commit install`)
4. Make your changes and ensure tests pass
5. Run linters and formatters
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide (enforced by Black and Flake8)
- Use type hints for all function signatures
- Write docstrings for all public APIs (Google style)
- Maintain test coverage above 40%
- Use meaningful variable and function names
- Keep functions small and focused (single responsibility)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Python](https://www.python.org/)
- Data validation with [Pydantic](https://pydantic-docs.helpmanual.io/)
- Testing with [pytest](https://pytest.org/)
- API clients for [Binance](https://www.binance.com/), [Coinbase](https://www.coinbase.com/), and [Kraken](https://www.kraken.com/)
- Market data from [CoinGecko](https://www.coingecko.com/)

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/saracevic/Trade/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/saracevic/Trade/discussions)
- 📧 Email: Open an issue for support

## 🔄 Changelog

### Version 2.0.0 (2025-12-27)

- ✨ Complete project modernization and restructuring
- 🏗️ Modular architecture with professional src/ structure
- ✅ Comprehensive test suite (31+ tests, 40% coverage)
- 🐳 Docker and docker-compose support
- 📝 Professional documentation with detailed guides
- 🔧 Complete CI/CD pipeline with automated testing
- 🎨 Code formatting and linting with pre-commit hooks
- 🔒 Type safety with Pydantic models
- 📊 Multiple export formats (JSON, CSV)
- ⚡ Async/await support for better performance
- 🌐 Professional web interface with responsive design
- 📈 Multi-exchange support (Binance, Coinbase, Kraken)
- 🚀 Automated daily scans with GitHub Actions

---

Made with ❤️ by the Trade Bot Development Team