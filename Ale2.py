import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# 1. CONFIGURACIÓN DE SEGURIDAD
symbol = 'ETHUSDT'

def ejecutar_gladiador():
    # Recuperamos las llaves que ya tenés cargadas en Railway
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    print("🚀 INICIANDO SISTEMA ALE-IA-QUANTUM...")
    
    try:
        client = Client(api_key, api_secret)
        # Test de conexión rápido
        client.futures_ping()
        print("⚔️ CONEXIÓN EXITOSA CON BINANCE FUTURES")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO DE LLAVES O REGIÓN: {e}")
        return

    while True:
        try:
            # 2. CARGA DE DATOS (300 VELAS PARA PRECISIÓN)
            k = client.futures_klines(symbol=symbol, interval='5m', limit=300)
            df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # ADX PROFESIONAL (Filtro de tendencia)
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

            # 4. LÓGICA DE OPERACIÓN
            dec = "ESPERAR"
            if adx > 25:
                if p_act > ema and p_di > m_di: dec = "LONG"
                elif p_act < ema and m_di > p_di: dec = "SHORT"

            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Señal: {dec} | Pos: {amt}")

            # 5. GESTIÓN DE CAPITAL (20% COMPUESTO X10)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                # Buscamos el saldo USDT disponible
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                
                # Cantidad = (Capital * 20% * 10 apalancamiento) / precio
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                
                # ESCUDO TRAILING 0.9% (Distancia 9 en callbackRate)
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=symbol, 
                    side=inv, 
                    type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, 
                    quantity=qty, 
                    reduceOnly=True
                )
                print(f"🚀 ENTRADA EJECUTADA: {dec} | Qty: {qty} | Trailing: 0.9%")

        except Exception as e:
            print(f"⚠️ Aviso de Ciclo: {e}")
            time.sleep(10)
        
        # Obligamos a Railway a mostrar el log
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    ejecutar_gladiador()
