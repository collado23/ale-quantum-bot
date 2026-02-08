import os
import time
import pandas as pd
from binance.client import Client
from binance.enums import *

# --- CONEXIÓN ORIGINAL (Asegurada) ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = 'ETHUSDT'
leverage = 10
capital_percent = 0.20 

def obtener_datos():
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=300)
    df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
    df['close'] = df['close'].astype(float)
    return df

def ejecutar_gladiador():
    print(f"🔱 ALE2.py - VERSIÓN ESTABLE - MACD MANUAL + 0.5% TRAILING")
    
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except:
        pass

    while True:
        try:
            df = obtener_datos()
            
            # --- CÁLCULO MANUAL (Sin librerías extra para evitar errores de Railway) ---
            # 1. EMA 200
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # 2. MACD MANUAL (12, 26, 9)
            ema_12 = df['close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            
            macd_l = macd_line.iloc[-1]
            macd_s = macd_signal.iloc[-1]
            
            precio = df['close'].iloc[-1]
            distancia = ((precio - ema_200) / ema_200) * 100
            
            # --- ESTADO DE POSICIÓN ---
            pos = client.futures_position_information(symbol=symbol)
            en_vuelo = float(pos[0]['positionAmt']) != 0

            if not en_vuelo:
                # SHORT: Distancia negativa y MACD bajista (Línea debajo de Señal)
                if distancia < -9 and macd_l < macd_s:
                    balance = float(client.futures_account_balance()[1]['balance'])
                    qty = (balance * capital_percent * leverage) / precio
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=round(qty, 3))
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type='TRAILING_STOP_MARKET', quantity=round(qty, 3), callbackRate=0.5, workingType='MARK_PRICE')
                    print(f"✅ SHORT DISPARADO EN {precio}")

                # LONG: Distancia positiva y MACD alcista (Línea arriba de Señal)
                elif distancia > 9 and macd_l > macd_s:
                    balance = float(client.futures_account_balance()[1]['balance'])
                    qty = (balance * capital_percent * leverage) / precio
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=round(qty, 3))
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type='TRAILING_STOP_MARKET', quantity=round(qty, 3), callbackRate=0.5, workingType='MARK_PRICE')
                    print(f"✅ LONG DISPARADO EN {precio}")
                else:
                    print(f"🔎 ETH: {precio} | Dist: {distancia:.1f}% | MACD: {'OK' if (macd_l < macd_s) else 'ESPERAR'}")
            else:
                print(f"🛡️ POSICIÓN ACTIVA EN {precio} - MONITOREANDO")

            time.sleep(30)

        except Exception as e:
            print(f"⚠️ Reintentando conexión: {e}")
            time.sleep(20)

if __name__ == "__main__":
    ejecutar_gladiador()
