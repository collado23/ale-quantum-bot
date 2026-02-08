import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# CONFIGURACIÓN INICIAL
symbol = 'ETHUSDT'
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

def obtener_cliente():
    try:
        return Client(api_key, api_secret)
    except Exception as e:
        print(f"❌ Error crítico de conexión: {e}")
        return None

def analizar_mercado(client):
    try:
        # Pedimos pocos datos para que sea ultra rápido
        k = client.futures_klines(symbol=symbol, interval='5m', limit=50)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        # EMA 200
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # ADX Rápido
        p_dm = (df['high'].diff()).clip(lower=0)
        m_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
        atr = tr.rolling(14).mean()
        p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
        m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
        adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        return p_act, ema, adx, p_di, m_di
    except:
        return None, None, None, None, None

def ejecutar_gladiador():
    client = obtener_cliente()
    if not client: return
    
    print(f"⚔️ Gladiador ETH en Alemania: SISTEMA REFORZADO")

    while True:
        try:
            # PARTE 1: ANALIZAR
            p_act, ema, adx, p_di, m_di = analizar_mercado(client)
            
            if p_act is None:
                print("⏳ Binance ocupado... reintentando en 10s")
                time.sleep(10)
                continue

            # PARTE 2: REVISAR POSICIÓN
            pos = client.futures_position_information(symbol=symbol)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == symbol)
            
            # PARTE 3: DECIDIR
            dec = "ESPERAR"
            if adx > 25:
                if p_act > ema and p_di > m_di: dec = "LONG"
                elif p_act < ema and m_di > p_di: dec = "SHORT"
            
            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Señal: {dec} | Pos: {amt}")

            # PARTE 4: OPERAR (20% Compuesto + Escudo 0.9)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p_act, 3) # x10 leverage
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                
                # ESCUDO TRAILING
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=symbol, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🚀 ENTRADA EJECUTADA: {dec}")

        except Exception as e:
            print(f"⚠️ Nota: {e}")
            time.sleep(5) # Evita el bucle infinito de errores
        
        sys.stdout.flush()
        time.sleep(20) # Pausa de seguridad

if __name__ == "__main__":
    ejecutar_gladiador()
