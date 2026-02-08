import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# 1. CONFIGURACIÓN
symbol = 'ETHUSDT'

def ejecutar():
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    print("🚀 GLADIADOR ALE-QUANTUM: MODO BLINDADO")
    
    try:
        client = Client(api_key, api_secret)
        client.futures_ping()
        print("⚔️ MOTOR CONECTADO A BINANCE")
    except Exception as e:
        print(f"❌ ERROR API: {e}")
        return

    while True:
        try:
            # 2. CAPTURA DE DATOS
            k = client.futures_klines(symbol=symbol, interval='5m', limit=450)
            
            # Verificamos que tengamos suficientes velas antes de seguir
            if len(k) < 300:
                print(f"⏳ Calentando motores... ({len(k)}/300 velas)")
                time.sleep(10)
                continue

            df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['c'] = df['c'].astype(float)
            df['h'] = df['h'].astype(float)
            df['l'] = df['l'].astype(float)

            # 3. INDICADORES
            p_act = df['c'].iloc[-1]
            ema = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # ADX
            p_dm = (df['h'].diff()).clip(lower=0)
            m_dm = (-df['l'].diff()).clip(lower=0)
            tr = np.maximum(df['h']-df['l'], np.maximum(abs(df['h']-df['c'].shift(1)), abs(df['l']-df['c'].shift(1))))
            atr = tr.rolling(14).mean()
            p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
            m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

            # 4. POSICIÓN Y CAPITAL
            pos = client.futures_position_information(symbol=symbol)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == symbol)

            # 5. LÓGICA DE TRADING
            dec = "ESPERAR"
            if adx > 25:
                if p_act > ema and p_di > m_di: dec = "LONG"
                elif p_act < ema and m_di > p_di: dec = "SHORT"

            # Log scannable
            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Señal: {dec} | Pos: {amt}")

            # 6. EJECUCIÓN (20% Capital x10)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                
                # Cantidad exacta para evitar errores de precisión
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                if qty < 0.001: qty = 0.001
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                
                # STOP LOSS TRAILING 0.9%
                time.sleep(2)
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=symbol, side=inv, type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, quantity=qty, reduceOnly=True
                )
                print(f"🔥 ORDEN DISPARADA: {dec}")

        except Exception as e:
            # Este es el escudo que evita que el bot se apague
            print(f"📡 Aviso: {e}")
            time.sleep(10)
        
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    ejecutar()
