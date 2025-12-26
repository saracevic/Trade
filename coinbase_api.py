"""Minimal Coinbase Exchange API helpers (public endpoints).
"""
import time
import requests

BASE = "https://api.exchange.coinbase.com"
session = requests.Session()
session.headers.update({"Accept": "application/json", "User-Agent": "trade-scanner/1.0"})

def _get(path, params=None, retry=3):
    url = BASE + path
    for _ in range(retry):
        r = session.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        time.sleep(0.3)
    r.raise_for_status()

def products():
    return _get('/products')

def product_stats(product_id):
    return _get(f'/products/{product_id}/stats')

def klines(product_id, granularity=60, start=None, end=None):
    # returns list of [time, low, high, open, close, volume] per Coinbase API
    params = {'granularity': granularity}
    if start is not None:
        params['start'] = start
    if end is not None:
        params['end'] = end
    return _get(f'/products/{product_id}/candles', params=params)
