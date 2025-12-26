# Trade Scanner

This project scans Binance USDT perpetual futures for two conditions:
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