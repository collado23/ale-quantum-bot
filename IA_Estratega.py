import pandas as pd
import numpy as np

def analizar_mercado(client, simbolo):
    try:
        k = client.futures_klines(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        p_act = df['close'].iloc[-1]
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # --- CÁLCULO DE ADX MANUAL (PARA EVITAR LA X EN GITHUB) ---
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
             np.maximum(abs(df['high'] - df['close'].shift(1)), 
             abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx = (100 * abs(plus_di - minus_di) / (plus_di + minus_di)) if (plus_di + minus_di) != 0 else 0
        
        # --- LÍNEA DE VOLUMEN ---
        depth = client.futures_order_book(symbol=simbolo, limit=50)
        v_c = sum(float(b[1]) for b in depth['bids'])
        v_v = sum(float(a[1]) for a in depth['asks'])
        vol_dif = v_c - v_v
        
        res = "ESPERAR"
        # Modificamos los precios de la X (Si ADX > 25, hay tendencia)
        if adx > 25:
            if p_act > ema and plus_di > minus_di and v_c > v_v:
                res = "LONG"
            elif p_act < ema and minus_di > plus_di and v_v > v_c:
                res = "SHORT"
        
        return res, p_act, adx, vol_dif
    except:
        return "ERROR", 0, 0, 0
