import pandas as pd
import numpy as np

def analizar_mercado(client, simbolo):
    try:
        k = client.futures_klines(symbol=simbolo, interval='5m', limit=300)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        p_act = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_dm = df['high'].diff().clip(lower=0)
        m_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        p_di = 100 * (p_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (m_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        depth = client.futures_order_book(symbol=simbolo, limit=500)
        v_c = sum(float(b[1]) for b in depth['bids'])
        v_v = sum(float(a[1]) for a in depth['asks'])
        res = "ESPERAR"
        if p_act > (ema_200 + 0.5) and p_di > (m_di + 12) and adx > 25 and v_c > v_v: res = "LONG"
        elif p_act < (ema_200 - 0.5) and m_di > (p_di + 12) and adx > 25 and v_v > v_c: res = "SHORT"
        return res, p_act, v_c, v_v
    except: return "ERROR", 0, 0, 0
