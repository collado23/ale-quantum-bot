import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# 1. CONFIGURACIÓN FIJA
symbol = 'ETHUSDT'

def ejecutar():
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    print("🚀 GLADIADOR ALE-QUANTUM: MODO TANQUE 26/9")
    
    try:
        client = Client(api_key, api_secret)
        client.futures_ping() # Conexión rápida
    except Exception as e:
        print(f"❌ Error API: {e}"); return

    while True:
        try:
            # 2. CAPTURA VELOZ (Bajamos a 400 velas para que Railway no se canse)
            k = client.futures_klines(symbol=symbol, interval='5m', limit=400)
            
            df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['c'] = df['c'].astype(float)
            df['h'] = df['h'].astype(float)
            df['l'] = df['l'].astype(float)

            # 3. CÁLCULOS (EMA y ADX)
            p_act = df['c'].iloc[-1]
            ema = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_real = p_act - ema
            
            # ADX Profesional
            p_dm = (df['h'].diff()).clip(lower=0)
            m_dm = (-df['l'].diff()).clip(lower=0)
            tr = np.maximum(df['h']-df['l'], np.maximum(abs(df['h']-df['c'].shift(1)), abs(df['l']-df['c'].shift(1))))
            atr = tr.rolling(14).mean()
            p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
            m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

            # 4. ZIGZAG TANQUE (Mira si la vela actual cerró arriba o abajo de la anterior)
            zz = "SUBE" if df['c'].iloc[-1] > df['c'].iloc[-2] else "BAJA"

            # 5. SALDO Y POSICIÓN
            bal = client.futures_account_balance()
            cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
            pos = client.futures_position_information(symbol=symbol)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == symbol)

            # 6. LÓGICA ALE (ADX 26 | DISTANCIA 9)
            dec = "ESPERAR"
            if adx > 26 and abs(dist_real) > 9:
                if p_act > ema and zz == "SUBE": dec = "LONG"
                elif p_act < ema and zz == "BAJA": dec = "SHORT"

            # TABLERO TOTAL (Lo que vos querías ver)
            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Dist: {round(dist_real,1)} | Cap: {round(cap,2)} | {dec}")

            # 7. EJECUCIÓN
            if amt == 0 and dec in ["LONG", "SHORT"]:
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                if qty < 0.001: qty = 0.001
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                
                time.sleep(2)
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=symbol, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🔥 DISPARO: {dec}")

        except Exception as e:
            print(f"📡 Aviso: {e}")
            time.sleep(5)
        
        sys.stdout.flush() # Esto es clave para que Railway no oculte el texto
        time.sleep(20)

if __name__ == "__main__":
    ejecutar()
