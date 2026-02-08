import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# ==========================================
# CEREBRO: ADX 25 + VOLUMEN + EMA 200
# ==========================================
def analizar_mercado(client, simbolo):
    try:
        k = client.futures_klines(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        p_act = df['close'].iloc[-1]
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # ADX Manual (Filtro > 25 para evitar zigzag)
        p_dm = (df['high'].diff()).clip(lower=0)
        m_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
        atr = tr.rolling(14).mean()
        p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
        m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
        adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        # Volumen
        depth = client.futures_order_book(symbol=simbolo, limit=50)
        v_c = sum(float(b[1]) for b in depth['bids'])
        v_v = sum(float(a[1]) for a in depth['asks'])
        
        res = "ESPERAR"
        if adx > 25:
            if p_act > ema and p_di > m_di and v_c > v_v: res = "LONG"
            elif p_act < ema and m_di > p_di and v_v > v_c: res = "SHORT"
            
        return res, p_act, adx
    except:
        return "ERROR", 0, 0

# ==========================================
# MOTOR: INTERÉS 20% + DISTANCIA 9 (0.9%)
# ==========================================
def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ Gladiador ETH: Conexión Exitosa (CÓDIGO ÚNICO)")
    except: return

    while True:
        try:
            dec, p, adx = analizar_mercado(client, sym)
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            print(f"🔎 ETH:{p} | ADX:{round(adx,1)} | Señal:{dec} | Pos:{amt}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                # Interés compuesto 20%
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # ESCUDO DISTANCIA 9
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=sym, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🚀 Entrada {dec} con Escudo 0.9% (Distancia 9)")

        except Exception as e:
            print(f"⚠️ Reintentando... {e}")
        
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    ejecutar_sistema()
