# Contributing to Trade Scanner

Thank you for your interest in contributing to Trade Scanner! This document provides guidelines and best practices for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. **Fork the Repository**: Click the "Fork" button in the top-right corner of the repository page.

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Trade.git
   cd Trade
   ```

3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/saracevic/Trade.git
   ```

4. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running the Project

```bash
# Run the scanner
python main.py

# Run with debug logging
python main.py --log-level DEBUG

# Run the legacy scanner
python scanner.py
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length**: Maximum 100 characters (enforced by Black)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single quotes for string literals in code
- **Imports**: Organized using isort (stdlib, third-party, local)

### Code Formatting

We use automated tools to maintain consistent code style:

#### Black (Code Formatter)

```bash
# Format all Python files
black src/ tests/ main.py

# Check formatting without making changes
black --check src/ tests/ main.py
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
```

#### isort (Import Sorter)

```bash
# Sort imports
isort src/ tests/ main.py

# Check import sorting
isort --check-only src/ tests/ main.py
```

Configuration in `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
line_length = 100
```

#### Flake8 (Linter)

```bash
# Lint all files
flake8 src/ tests/ main.py

# Lint specific file
flake8 src/scanner/core.py
```

Configuration in `pyproject.toml`:
```toml
[tool.flake8]
max-line-length = 100
extend-ignore = ["E203", "W503"]
```

#### mypy (Type Checker)

```bash
# Type check all files
mypy src/

# Type check specific file
mypy src/scanner/core.py
```

### Docstring Style

We use **Google Style** docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function.
    
    More detailed description if needed. Explain what the function does,
    any important behavior, or usage notes.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Type Hints

All function signatures must include type hints:

```python
from typing import List, Dict, Optional, Any

def scan_exchange(
    exchange: str,
    filters: Optional[Dict[str, Any]] = None
) -> List[TradingPair]:
    """Function with proper type hints."""
    pass
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `TradeScanner`, `BinanceAPI`)
- **Functions/Methods**: snake_case (e.g., `scan_exchange`, `get_ticker`)
- **Variables**: snake_case (e.g., `trading_pairs`, `api_key`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `BASE_URL`, `DEFAULT_TIMEOUT`)
- **Private Methods**: Prefix with underscore (e.g., `_validate_data`)

### Error Handling

Always use specific exception types and provide meaningful error messages:

```python
# Good
try:
    result = api.get_ticker(symbol)
except requests.exceptions.Timeout:
    logger.error(f"Timeout fetching ticker for {symbol}")
    raise
except requests.exceptions.RequestException as e:
    logger.error(f"Request failed for {symbol}: {e}")
    raise

# Bad
try:
    result = api.get_ticker(symbol)
except Exception:
    pass  # Never silently catch exceptions
```

### Logging

Use appropriate log levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for unexpected situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical issues requiring immediate attention

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Fetching data from API")
logger.info("Scan completed successfully")
logger.warning("Rate limit approaching")
logger.error("Failed to connect to exchange")
logger.critical("Critical configuration missing")
```

## Testing Guidelines

### Test Structure

We use **pytest** for testing:

```python
import pytest
from src.api.binance import BinanceAPI

def test_binance_exchange_info():
    """Test that exchange info can be fetched."""
    api = BinanceAPI()
    info = api.get_exchange_info()
    assert info is not None
    assert 'symbols' in info

@pytest.mark.asyncio
async def test_async_scanner():
    """Test async scanner functionality."""
    scanner = TradeScanner(config)
    results = await scanner.scan_all_exchanges()
    assert results is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::test_binance_exchange_info
```

### Test Coverage

- Aim for **40%+ overall coverage** (current standard)
- All new features must include tests
- Bug fixes should include regression tests

### Test Fixtures

Use pytest fixtures for reusable test data:

```python
@pytest.fixture
def sample_config():
    """Provide a sample configuration for tests."""
    return ScannerConfig(
        api_keys={"binance": "test_key"},
        api_secrets={"binance": "test_secret"},
        min_volume=1000.0
    )
```

## Pull Request Process

### Before Submitting

1. **Sync with Upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run All Checks**:
   ```bash
   # Format code
   black src/ tests/ main.py
   isort src/ tests/ main.py
   
   # Run linters
   flake8 src/ tests/ main.py
   mypy src/
   
   # Run tests
   pytest --cov=src
   
   # Run pre-commit hooks
   pre-commit run --all-files
   ```

3. **Update Documentation**: Ensure all changes are documented.

### Commit Messages

Write clear, descriptive commit messages:

```
feat: Add CSV export functionality to web interface

- Add export button to UI
- Implement CSV generation from filtered results
- Add translations for export button

Closes #123
```

Commit message format:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All CI checks passing
```

## Project Structure

```
Trade/
├── src/                    # Source code (modular architecture)
│   ├── api/               # Exchange API clients
│   ├── scanner/           # Scanner logic
│   ├── models/            # Data models (Pydantic)
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── config/                # Configuration
├── .github/workflows/     # CI/CD workflows
├── main.py                # Modern CLI entry point
├── scanner.py             # Legacy scanner
└── index.html             # Web interface
```

## Best Practices

### 1. Keep It Simple

- Write simple, readable code
- Avoid premature optimization
- Follow KISS (Keep It Simple, Stupid) principle

### 2. Single Responsibility

- Each function should do one thing well
- Keep functions small (< 50 lines ideally)
- Extract complex logic into separate functions

### 3. DRY (Don't Repeat Yourself)

- Avoid code duplication
- Extract common logic into utilities
- Use inheritance and composition appropriately

### 4. Documentation

- Document all public APIs
- Keep comments up-to-date
- Explain "why", not "what"

### 5. Error Handling

- Handle errors gracefully
- Provide meaningful error messages
- Log errors appropriately
- Never silently catch exceptions

## Questions or Issues?

If you have questions or encounter issues:

1. Check existing [Issues](https://github.com/saracevic/Trade/issues)
2. Search [Discussions](https://github.com/saracevic/Trade/discussions)
3. Open a new issue with a clear description

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Trade Scanner! 🚀
