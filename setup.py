"""
Setup script for Trade Scanner.
For modern installation, use: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="trade-scanner",
    version="2.0.0",
    description="Professional multi-exchange cryptocurrency trading pair scanner",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Trade Bot Development Team",
    author_email="trade@example.com",
    url="https://github.com/saracevic/Trade",
    license="MIT",
    packages=find_packages(),
    package_dir={"": "."},
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "pytz>=2023.3",
        "python-dateutil>=2.8.2",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=0.19.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "types-requests>=2.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "trade-scanner=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="cryptocurrency trading scanner binance coinbase kraken",
    project_urls={
        "Documentation": "https://github.com/saracevic/Trade#readme",
        "Source": "https://github.com/saracevic/Trade",
        "Tracker": "https://github.com/saracevic/Trade/issues",
    },
)
