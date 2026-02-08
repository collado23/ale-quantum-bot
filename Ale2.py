import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# 1. CONFIGURACIÓN
symbol = 'ETHUSDT'

def ejecutar_gladiador():
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    print("🚀 INICIANDO SISTEMA REFORZADO...")
    
    try:
        client = Client(api_key, api_secret)
        client.futures_ping()
        print("⚔️ CONEXIÓN EXITOSA - EL MOTOR ESTÁ VIVO")
    except Exception as e:
        print(f"❌ ERROR API: {e}")
        return

    while True:
        try:
            # 2. DATOS (300 VELAS)
            k = client.futures_klines(symbol=symbol, interval='5m', limit=300)
            df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # ADX
            p_dm = (df['high'].diff()).clip(lower=0)
            m_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
            atr = tr.rolling(14).mean()
            p_di = 100 * (p_dm.rolling(14).mean() / atr).iloc[-1]
            m_di = 100 * (m_dm.rolling(14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

            # 3. ESTADO DE POSICIÓN
            pos = client.futures_position_information(symbol=symbol)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == symbol)

            # 4. LÓGICA
            dec = "ESPERAR"
            if adx > 25:
                if p_act > ema and p_di > m_di: dec = "LONG"
                elif p_act < ema and m_di > p_di: dec = "SHORT"

            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Señal: {dec} | Pos: {amt}")

            # 5. GESTIÓN DE ORDEN (Protección contra cierres)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                
                # Ajuste de cantidad (mínimo 0.001 ETH para Binance)
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                if qty < 0.001: qty = 0.001
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                
                # Ejecutar entrada
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                print(f"🚀 ENTRADA: {dec} de {qty} ETH")
                
                time.sleep(2) # Respiro para Binance
                
                # Escudo Trailing 0.9%
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=symbol, 
                    side=inv, 
                    type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, 
                    quantity=qty, 
                    reduceOnly=True
                )
                print("🛡️ ESCUDO ACTIVADO")

        except Exception as e:
            # ESTO ES CLAVE: Si hay un error, el bot NO se apaga, solo avisa.
            print(f"⚠️ Nota de sistema: {e}")
            time.sleep(15)
        
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    ejecutar_gladiador()
