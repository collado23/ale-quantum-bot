import pandas as pd
import numpy as np

def analizar_mercado(client, simbolo):
    """Analiza 300 velas y 500 puntas del libro para dar una orden"""
    try:
        # 📊 1. Análisis de Velas y DMI
        klines = client.futures_klines(symbol=simbolo, interval='5m', limit=300)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        p_act = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # Cálculos de Fuerza (DMI / ADX)
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

        # 📚 2. Análisis de 500 Puntas del Libro
        depth = client.futures_order_book(symbol=simbolo, limit=500)
        v_c = sum(float(b[1]) for b in depth['bids'])
        v_v = sum(float(a[1]) for a in depth['asks'])

        # 🎯 3. Decisión Final
        if p_act > (ema_200 + 1) and p_di > (m_di + 12) and adx > 25 and v_c > v_v:
            return "LONG", p_act, v_c, v_v
        elif p_act < (ema_200 - 1) and m_di > (p_di + 12) and adx > 25 and v_v > v_c:
            return "SHORT", p_act, v_c, v_v
        
        return "ESPERAR", p_act, v_c, v_v
        
    except Exception as e:
        print(f"🧠 Error en Estratega: {e}")
        return "ERROR", 0, 0, 0
