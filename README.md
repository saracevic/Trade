# Trade Scanner

- Friday Asian-range 50% midline (script's `midline_body`) touch after session end
- 50% Fibonacci (from ATH/ATL via daily candles) touches after session end

It uses public Binance Futures API and writes results to `out/results.json`.

Usage (local):

```bash
python -m pip install -r requirements.txt
python scanner.py
```

You can run this daily with GitHub Actions; an example workflow is included in `.github/workflows/scan.yml` to push results to `gh-pages`.

Supported exchanges (best-effort): `binance` (futures), `coinbase`, `kraken`. The scanner will try to fetch top symbols per exchange and apply the same Asia-range midline + fib50 checks. Results are aggregated to `out/results.json` and published to GitHub Pages.

To run a manual full top-200 scan and publish via Actions, use the `Manual Scan and publish` workflow from the Actions tab (or click "Run Scan" on the site and trigger the workflow).

- Friday Asian-range 50% midline (script's `midline_body`) touch after session end
- 50% Fibonacci (from ATH/ATL via daily candles) touches after session end

It uses public Binance Futures API and writes results to `out/results.json`.

Usage (local):

```bash
python -m pip install -r requirements.txt
python scanner.py
```

You can run this daily with GitHub Actions; an example workflow is included in `.github/workflows/scan.yml` to push results to `gh-pages`.
# Trade