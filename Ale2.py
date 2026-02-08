import os
import time
import pandas as pd

# 1. Instalación forzada para evitar errores de librería
try:
    import pandas_ta as ta
except ImportError:
    os.system('pip install pandas-ta')
    import pandas_ta as ta

from binance.client import Client
from binance.enums import *

# --- 2. CONEXIÓN BLINDADA ---
api_key = os.environ.get('BINANCE_API_KEY')
api_secret = os.environ.get('BINANCE_API_SECRET')

# Verificación de seguridad para los logs
if not api_key or not api_secret:
    print("❌ ERROR CRÍTICO: Railway no está cargando tus API KEYS.")
    print("👉 Andá a 'Settings' > 'Variables' y revisá que los nombres estén BIEN.")
else:
    print("✅ API Keys detectadas. Conectando con Binance...")

client = Client(api_key, api_secret)

symbol = 'ETHUSDT'
leverage = 10
capital_percent = 0.20 

def obtener_datos():
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=300)
    df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df

def ejecutar_gladiador():
    print(f"🔱 ALE2.py - MODO RECUPERACIÓN - {symbol}")
    
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except Exception as e:
        print(f"⚠️ Nota de conexión: {e}")

    while True:
        try:
            df = obtener_datos()
            
            # --- INDICADORES ---
            df['ema_200'] = ta.ema(df['close'], length=200)
            ema_val = df['ema_200'].iloc[-1]
            
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            adx_val = adx_df['ADX_14'].iloc[-1]
            
            # MACD para el escudo de picos
            macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
            macd_l = macd_df['MACD_12_26_9'].iloc[-1]
            macd_s = macd_df['MACDs_12_26_9'].iloc[-1]
            
            precio = df['close'].iloc[-1]
            distancia = ((precio - ema_val) / ema_val) * 100
            
            # --- REVISIÓN DE POSICIÓN ---
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next(p for p in pos if p['symbol'] == symbol)
            en_posicion = float(datos_pos['positionAmt']) != 0

            if not en_posicion:
                # SHORT
                if adx_val > 26 and distancia < -9 and macd_l < macd_s:
                    balance = float(client.futures_account_balance()[1]['balance'])
                    qty = (balance * capital_percent * leverage) / precio
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=round(qty, 3))
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type='TRAILING_STOP_MARKET', quantity=round(qty, 3), callbackRate=0.5, workingType='MARK_PRICE')
                    print(f"✅ SHORT ABIERTO")
                
                # LONG
                elif adx_val > 26 and distancia > 9 and macd_l > macd_s:
                    balance = float(client.futures_account_balance()[1]['balance'])
                    qty = (balance * capital_percent * leverage) / precio
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=round(qty, 3))
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type='TRAILING_STOP_MARKET', quantity=round(qty, 3), callbackRate=0.5, workingType='MARK_PRICE')
                    print(f"✅ LONG ABIERTO")
                else:
                    print(f"🔎 ETH: {precio} | ADX: {adx_val:.1f} | MACD: OK | ESPERAR")
            else:
                print(f"🛡️ POSICIÓN ACTIVA - MONITOREANDO {precio}")

            time.sleep(30)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    ejecutar_gladiador()
