import requests
from typing import List, Dict, Optional

BASE = "https://api.coingecko.com/api/v3"


def _get(path: str, params: Optional[dict] = None, timeout: int = 20):
    url = f"{BASE}{path}"
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def coins_markets(vs_currency: str = "usd", per_page: int = 250, page: int = 1, order: str = "market_cap_desc") -> List[Dict]:
    params = {"vs_currency": vs_currency, "order": order, "per_page": per_page, "page": page, "sparkline": "false"}
    return _get("/coins/markets", params=params)


def market_chart_range(coin_id: str, vs_currency: str, from_ts: int, to_ts: int) -> Dict:
    params = {"vs_currency": vs_currency, "from": int(from_ts), "to": int(to_ts)}
    return _get(f"/coins/{coin_id}/market_chart/range", params=params)


def map_coin_to_perp(exchange_api, coin_symbol: str) -> List[str]:
    """
    Try to map a base coin symbol (e.g. BTC) to candidate perpetual symbols on the given exchange API.

    The exchange_api object should expose either `exchange_info()` (Binance-style) or `products()`/`products` (Coinbase-style).
    This function is best-effort and returns possible symbol strings (de-duplicated).
    """
    candidates: List[str] = []
    coin_symbol = coin_symbol.upper()

    # Try exchange_info() -> { 'symbols': [ { 'symbol': 'BTCUSDT', ...}, ... ] }
    try:
        info = exchange_api.exchange_info()
        symbols = None
        if isinstance(info, dict):
            symbols = info.get("symbols") or info.get("symbolsList")
        elif isinstance(info, list):
            symbols = info
        if symbols and isinstance(symbols, list):
            for s in symbols:
                sym = None
                if isinstance(s, dict):
                    sym = s.get("symbol") or s.get("pair")
                elif isinstance(s, str):
                    sym = s
                if not sym:
                    continue
                usdt_like = ("USDT" in sym.upper()) or ("USD" in sym.upper())
                if sym.upper().startswith(coin_symbol) and usdt_like:
                    # Prefer perpetual contract if contract type present
                    if isinstance(s, dict):
                        ct = s.get("contractType") or s.get("type") or ""
                        if ct and "PERP" in str(ct).upper():
                            candidates.append(sym.upper())
                            continue
                    candidates.append(sym.upper())
    except Exception:
        pass

    # Try generic products() (Coinbase style) -> list of dicts with 'id' or 'symbol'
    try:
        prods = None
        if hasattr(exchange_api, "products"):
            prods = exchange_api.products()
        elif hasattr(exchange_api, "products_list"):
            prods = exchange_api.products_list()
        if isinstance(prods, list):
            for p in prods:
                sym = None
                if isinstance(p, dict):
                    sym = p.get("id") or p.get("symbol") or p.get("name")
                elif isinstance(p, str):
                    sym = p
                if not sym:
                    continue
                su = sym.upper()
                if su.startswith(coin_symbol) and ("USDT" in su or "USD" in su):
                    candidates.append(su)
    except Exception:
        pass

    # De-duplicate preserving order
    seen = set()
    out: List[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out
