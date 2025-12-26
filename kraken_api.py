"""Minimal Kraken public API helpers.
"""
import time
import requests

BASE = "https://api.kraken.com"
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

def asset_pairs():
    return _get('/0/public/AssetPairs')

def ohlc(pair, interval=1, since=None):
    params = {'pair': pair, 'interval': interval}
    if since is not None:
        params['since'] = since
    data = _get('/0/public/OHLC', params=params)
    return data
