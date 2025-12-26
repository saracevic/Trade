"""Minimal Binance Futures (USDT-M) helper using public endpoints.
"""
import time
import requests

BASE = "https://fapi.binance.com"

session = requests.Session()
session.headers.update({"Accept": "application/json"})

def _get(path, params=None, retry=3):
    url = BASE + path
    for _ in range(retry):
        r = session.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        time.sleep(0.3)
    r.raise_for_status()

def exchange_info():
    return _get('/fapi/v1/exchangeInfo')

def ticker_24h():
    return _get('/fapi/v1/ticker/24hr')

def klines(symbol, interval='1m', startTime=None, endTime=None, limit=1500):
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if startTime is not None:
        params['startTime'] = int(startTime)
    if endTime is not None:
        params['endTime'] = int(endTime)
    return _get('/fapi/v1/klines', params=params)

def klines_range(symbol, interval, start_ms, end_ms):
    # fetch in batches of max 1500 until end_ms
    data = []
    cur = int(start_ms)
    while cur < end_ms:
        batch = klines(symbol, interval=interval, startTime=cur, endTime=end_ms, limit=1500)
        if not batch:
            break
        data.extend(batch)
        last_open = batch[-1][0]
        # advance by one ms after last open to avoid duplicate
        cur = int(last_open) + 1
        time.sleep(0.12)
        # safety
        if len(batch) < 1500:
            break
    return data
