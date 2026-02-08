import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

symbol = 'ETHUSDT'

def calcular_zigzag(df, percentage=1):
    # Lógica simplificada de ZigZag para detectar tendencia de picos
    closes = df['c'].tolist()
    puntos = []
    for i in range(1, len(closes)-1):
        if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
            puntos.append(("MAX", closes[i]))
        elif closes[i] < closes[i-1] and closes[i] < closes[i+1]:
            puntos.append(("MIN", closes[i]))
    return puntos[-1] if puntos else ("NULO", 0)

def ejecutar():
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    print("🚀 GLADIADOR ALE-QUANTUM: MODO ZIG-ZAG 26/9")
    
    try:
        client = Client(api_key, api_secret)
    except Exception as e:
        print(f"❌ ERROR: {e}"); return

    while True:
        try:
            k = client.futures_klines(symbol=symbol, interval='5m', limit=450)
            df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['c'] = df['c'].astype(float)
            df['h'] = df['h'].astype(float)
            df['l'] = df['l'].astype(float)

            p_act = df['c'].iloc[-1]
            ema = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_abs = abs(p_act - ema)
            
            # ADX
            p_dm = (df['h'].diff()).clip(lower=0)
            m_dm = (-df['l'].diff()).clip(lower=0)
            tr = np.maximum(df['h']-df['l'], np.maximum(abs(df['h']-df['c'].shift(1)), abs(df['l']-df['c'].shift(1))))
            atr = tr.rolling(14).mean()
            p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
            m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

            # ZIG ZAG (Último punto de giro)
            tipo_zz, valor_zz = calcular_zigzag(df)

            bal = client.futures_account_balance()
            cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
            pos = client.futures_position_information(symbol=symbol)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == symbol)

            # LÓGICA REFORZADA: ADX + DISTANCIA + ZIGZAG
            dec = "ESPERAR"
            if adx > 26 and dist_abs > 9:
                # LONG: Precio > EMA y el último punto ZigZag fue un MIN (está subiendo)
                if p_act > ema and p_di > m_di and tipo_zz == "MIN":
                    dec = "LONG"
                # SHORT: Precio < EMA y el último punto ZigZag fue un MAX (está bajando)
                elif p_act < ema and m_di > p_di and tipo_zz == "MAX":
                    dec = "SHORT"

            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | ZZ: {tipo_zz} | Cap: {round(cap,1)} | {dec}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                if qty < 0.001: qty = 0.001
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                
                time.sleep(2)
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=symbol, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🔥 DISPARO CON ZIGZAG: {dec}")

        except Exception as e:
            print(f"📡 Aviso: {e}"); time.sleep(10)
        
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    ejecutar()
