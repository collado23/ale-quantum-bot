import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

def gladiador():
    sym = 'ETHUSDT'
    print("🚀 Motor Gladiador: ON")
    
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    try:
        client = Client(api_key, api_secret)
        client.futures_ping() # Solo para asegurar que responde
        print("⚔️ Conexión Exitosa con Binance Futures")
    except Exception as e:
        print(f"❌ Error de Conexión: {e}")
        return

    while True:
        try:
            # 1. Obtener datos con manejo de errores
            k = client.futures_klines(symbol=sym, interval='5m', limit=100)
            if not k:
                continue

            df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # ADX Manual
            p_dm = (df['high'].diff()).clip(lower=0)
            m_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
            atr = tr.rolling(14).mean()
            p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
            m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
            
            # 2. Estado de Posición
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            dec = "ESPERAR"
            if adx > 25:
                if p_act > ema and p_di > m_di: dec = "LONG"
                elif p_act < ema and m_di > p_di: dec = "SHORT"
            
            # ESTO ES LO QUE QUEREMOS VER
            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Señal: {dec} | Pos: {amt}")

            # 3. Operar (20% Compuesto + Escudo 0.9%)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=sym, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🚀 ENTRADA REALIZADA: {dec}")

        except Exception as e:
            # Si hay un error, el bot te dirá exactamente qué palabra falló
            print(f"⚠️ Aviso: {e}")
        
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    gladiador()
