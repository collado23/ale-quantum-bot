import pandas as pd
import numpy as np

def analizar_mercado(client, simbolo):
    try:
        # Traer velas de 5m
        k = client.futures_klines(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        p_act = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # --- CÁLCULO MANUAL ADX (Filtro 25) ---
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
        atr = tr.rolling(14).mean()
        p_di = 100 * (plus_dm.rolling(14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(14).mean() / atr).iloc[-1]
        adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        res = "ESPERAR"
        # Filtro de fuerza: Solo entra si ADX > 25
        if adx > 25:
            if p_act > ema_200 and p_di > m_di: res = "LONG"
            elif p_act < ema_200 and m_di > p_di: res = "SHORT"
            
        return res, p_act, adx, 0
    except:
        return "ERROR", 0, 0, 0
