"""Scanner that checks top USDT perpetuals for Asia-range midline touches and ATH/ATL fib touches.

Outputs JSON to ./out/results.json
"""
import time
import math
import json
from datetime import datetime, timedelta, timezone
import pytz
import pandas as pd

from binance_api import exchange_info, ticker_24h, klines, klines_range
from coinbase_api import products as cb_products, klines as cb_klines
from kraken_api import asset_pairs as kr_asset_pairs, ohlc as kr_ohlc

OUT_PATH = 'out/results.json'

def now_ms():
    return int(time.time() * 1000)

def to_ms(dt: datetime):
    return int(dt.timestamp() * 1000)

def fib_level(high, low, lvl, use_log=False, reverse=False):
    if math.isnan(high) or math.isnan(low):
        return None
    if use_log:
        lh = math.log(high)
        ll = math.log(low)
        if reverse:
            return math.exp(ll + (lh - ll) * lvl)
        else:
            return math.exp(lh - (lh - ll) * lvl)
    else:
        if reverse:
            return low + (high - low) * lvl
        else:
            return high - (high - low) * lvl

def parse_klines(raw):
    # raw kline list -> DataFrame
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw, columns=[
        'open_time','open','high','low','close','volume','close_time','qav','num_trades','taker_base','taker_quote','ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    for c in ['open','high','low','close','volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def find_last_friday_session(df_1m):
    # script uses Friday 19:00-23:59 America/New_York
    tz_ny = pytz.timezone('America/New_York')
    if df_1m.empty:
        return None
    df = df_1m.copy()
    df['local'] = df['open_time'].dt.tz_localize(pytz.UTC).dt.tz_convert(tz_ny)
    df['weekday'] = df['local'].dt.weekday  # Monday=0 ... Sunday=6
    df['hour'] = df['local'].dt.hour
    # Friday is weekday==4. Select bars between 19:00 and 23:59
    friday = df[(df['weekday'] == 4) & (df['hour'] >= 19) & (df['hour'] <= 23)]
    if friday.empty:
        return None
    # group by date of local date (NY) to find last Friday group
    friday['date'] = friday['local'].dt.date
    last_date = friday['date'].max()
    sess = friday[friday['date'] == last_date]
    if sess.empty:
        return None
    ar_start = sess['open_time'].min()
    ar_end = sess['open_time'].max() + pd.Timedelta(minutes=1)
    # bodyHigh: max of max(open,close)
    body_high = max(sess['open'].max(), sess['close'].max(), sess['high'].max())
    body_low = min(sess['open'].min(), sess['close'].min(), sess['low'].min())
    wick_high = sess['high'].max()
    wick_low = sess['low'].min()
    return dict(start=ar_start.isoformat(), end=ar_end.isoformat(), body_high=float(body_high), body_low=float(body_low), wick_high=float(wick_high), wick_low=float(wick_low))

def touched_after(df_after, price):
    # check if any candle after session touches price (low<=price<=high)
    if df_after.empty:
        return None
    touched = df_after[(df_after['low'] <= price) & (df_after['high'] >= price)]
    if touched.empty:
        return None
    row = touched.iloc[0]
    return dict(time=row['open_time'].isoformat(), price=float(price))

def scan_top_n(n=200, exchanges=('binance', 'coinbase', 'kraken')):
    """Scan top symbols from multiple exchanges.
    For Binance we use futures top by quoteVolume. For Coinbase/Kraken we use product/asset list (best-effort top N per exchange).
    """
    results = []
    now = datetime.now(timezone.utc)
    start_fetch_ms = to_ms(now - timedelta(days=8))
    end_fetch_ms = to_ms(now + timedelta(minutes=1))

    for exch in exchanges:
        symbols = []
        try:
            if exch == 'binance':
                info = exchange_info()
                symbols_info = info.get('symbols', [])
                perp_usdt = [s['symbol'] for s in symbols_info if s.get('status') == 'TRADING' and s.get('symbol','').endswith('USDT') and ('PERPETUAL' in s.get('contractType','PERPETUAL'))]
                tickers = ticker_24h()
                tickers = [t for t in tickers if t['symbol'] in perp_usdt]
                tickers.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
                symbols = [t['symbol'] for t in tickers[:n]]
            elif exch == 'coinbase':
                prods = cb_products()
                # take product ids like BTC-USD, filter USD pairs
                prods = [p for p in prods if p.get('quote_currency') in ('USD','USDT','USDC')]
                symbols = [p['id'] for p in prods[:n]]
            elif exch == 'kraken':
                pairs = kr_asset_pairs().get('result', {})
                keys = list(pairs.keys())[:n]
                symbols = keys
        except Exception as e:
            print('symbol fetch error', exch, e)

        for sym in symbols:
            try:
                if exch == 'binance':
                    raw1 = klines_range(sym, '1m', start_fetch_ms, end_fetch_ms)
                    df1 = parse_klines(raw1)
                    session = find_last_friday_session(df1)
                    midline_touch = None
                    if session is not None:
                        mid = (session['body_high'] + session['body_low']) / 2.0
                        df_after = df1[df1['open_time'] > session['end']]
                        touch = touched_after(df_after, mid)
                        if touch:
                            midline_touch = touch
                    rawd = klines(sym, '1d', limit=1000)
                    dfd = parse_klines(rawd)
                    if not dfd.empty:
                        ath = float(dfd['high'].max())
                        atl = float(dfd['low'].min())
                    else:
                        ath = None
                        atl = None
                    fib50 = None
                    fib_touches = []
                    if ath and atl and ath > atl:
                        fib50 = fib_level(ath, atl, 0.5)
                        if session is not None:
                            df_after = df1[df1['open_time'] > session['end']]
                            touch = touched_after(df_after, fib50)
                            if touch:
                                fib_touches.append(dict(level=0.5, touch=touch))
                    results.append(dict(exchange=exch, symbol=sym, session=session, midline_touch=midline_touch, fib50=fib50, fib_touches=fib_touches, ath=ath, atl=atl))
                elif exch == 'coinbase':
                    # Coinbase product id like BTC-USD; use candles granularity 60s
                    raw = cb_klines(sym, granularity=60)
                    # Coinbase returns [time, low, high, open, close, volume]
                    df = parse_klines([[c[0]*1000, c[3], c[2], c[1], c[4], c[5], 0,0,0,0,0,0] for c in raw])
                    session = find_last_friday_session(df)
                    midline_touch = None
                    if session:
                        mid = (session['body_high'] + session['body_low']) / 2.0
                        df_after = df[df['open_time'] > session['end']]
                        touch = touched_after(df_after, mid)
                        if touch:
                            midline_touch = touch
                    # daily ATH/ATL via larger granularity
                    rawd = cb_klines(sym, granularity=86400)
                    if rawd:
                        dfd = parse_klines([[c[0]*1000, c[3], c[2], c[1], c[4], c[5], 0,0,0,0,0,0] for c in rawd])
                        ath = float(dfd['high'].max())
                        atl = float(dfd['low'].min())
                    else:
                        ath = atl = None
                    fib50 = fib_level(ath, atl, 0.5) if ath and atl and ath>atl else None
                    results.append(dict(exchange=exch, symbol=sym, session=session, midline_touch=midline_touch, fib50=fib50, fib_touches=[], ath=ath, atl=atl))
                elif exch == 'kraken':
                    # Kraken pair keys and OHLC
                    data = kr_ohlc(sym, interval=1)
                    if data and 'result' in data:
                        # result contains pair key and 'last'
                        pair_key = [k for k in data['result'].keys() if k != 'last'][0]
                        raw = data['result'][pair_key]
                        # raw items: [time, open, high, low, close, v, ...]
                        df = parse_klines([[int(c[0])*1000, c[1], c[2], c[3], c[4], c[6], 0,0,0,0,0,0] for c in raw])
                        session = find_last_friday_session(df)
                        midline_touch = None
                        if session:
                            mid = (session['body_high'] + session['body_low']) / 2.0
                            df_after = df[df['open_time'] > session['end']]
                            touch = touched_after(df_after, mid)
                            if touch:
                                midline_touch = touch
                        # daily ATH/ATL: aggregate by day
                        ath = df['high'].max() if not df.empty else None
                        atl = df['low'].min() if not df.empty else None
                        fib50 = fib_level(ath, atl, 0.5) if ath and atl and ath>atl else None
                        results.append(dict(exchange=exch, symbol=sym, session=session, midline_touch=midline_touch, fib50=fib50, fib_touches=[], ath=ath, atl=atl))
            except Exception as e:
                results.append(dict(exchange=exch, symbol=sym, error=str(e)))
            time.sleep(0.12)

    # save
    with open(OUT_PATH, 'w') as f:
        json.dump({'generated_at': datetime.now(timezone.utc).isoformat(), 'results': results}, f, indent=2)

if __name__ == '__main__':
    import os
    os.makedirs('out', exist_ok=True)
    print('Scanning top perpetuals...')
    scan_top_n(200)
    print('Saved to', OUT_PATH)
