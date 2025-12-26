# Trade Scanner

A cryptocurrency trading pair scanner that monitors multiple exchanges (Binance, Coinbase, Kraken) and publishes results to GitHub Pages.

## Features

- Scans multiple cryptocurrency exchanges for trading pairs
- Tracks price, volume, bid/ask spreads, and 24h changes
- Automatically publishes results to GitHub Pages
- Auto-updates every push to main branch
- Manual scan trigger available

## Live Demo

Visit the live scanner results at: **https://saracevic.github.io/Trade/**

## Usage

### Local Development

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run the scanner
python main.py
```

This will generate `results.json` with the latest trading data.

### GitHub Actions

The scanner runs automatically via GitHub Actions:

1. **Automatic Scan**: Triggers on every push to `main` branch (`.github/workflows/scan.yml`)
2. **Manual Scan**: Can be triggered manually from the Actions tab (`.github/workflows/manual_scan.yml`)

Both workflows will:
- Install dependencies
- Run the scanner
- Generate `results.json`
- Commit and push results back to the repository
- Update GitHub Pages automatically

## GitHub Pages Setup

To enable GitHub Pages for this repository:

1. Go to repository **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select branch: **main**
4. Select folder: **/ (root)**
5. Click **Save**

After a few minutes, your site will be live at `https://<username>.github.io/Trade/`

## Supported Exchanges

- **Binance** (Futures)
- **Coinbase**
- **Kraken**

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`:
  - requests
  - aiohttp
  - pydantic
  - python-dotenv
  - pandas
  - pytz

## Project Structure

```
.
├── .github/workflows/     # GitHub Actions workflows
├── src/                   # Source code
│   ├── api/              # Exchange API clients
│   ├── models/           # Data models
│   ├── scanner/          # Core scanner logic
│   └── utils/            # Utility functions
├── index.html            # GitHub Pages frontend
├── results.json          # Scanner output (auto-generated)
├── main.py              # Entry point
└── requirements.txt     # Python dependencies
```

## License

See [LICENSE](LICENSE) file for details.