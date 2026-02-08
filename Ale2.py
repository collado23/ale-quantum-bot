import os
import time

# --- TRUCO DE INSTALACIÓN AUTOMÁTICA ---
try:
    import pandas_ta as ta
except ImportError:
    print("📦 Instalando herramientas de análisis (pandas-ta)...")
    os.system('pip install pandas-ta')
    import pandas_ta as ta

import pandas as pd
from binance.client import Client
from binance.enums import *

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = 'ETHUSDT'
leverage = 10
capital_percent = 0.20  # Usamos el 20% de tu capital (aprox 6.9 USDT)

def obtener_datos():
    # Velas de 5 minutos
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=300)
    df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df

def ejecutar_gladiador():
    print(f"🔱 ALE2.py ACTUALIZADO - FILTRO MACD + TRAILING 0.5% - {symbol}")
    
    # Aseguramos el apalancamiento x10
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except Exception as e:
        print(f"⚠️ Nota sobre apalancamiento: {e}")

    while True:
        try:
            df = obtener_datos()
            
            # --- CÁLCULO DE INDICADORES ---
            # 1. EMA 200
            df['ema_200'] = ta.ema(df['close'], length=200)
            ema_val = df['ema_200'].iloc[-1]
            
            # 2. ADX (Fuerza)
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            adx_val = adx_df['ADX_14'].iloc[-1]
            
            # 3. MACD (El escudo contra picos)
            macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
            macd_line = macd_df['MACD_12_26_9'].iloc[-1]
            macd_signal = macd_df['MACDs_12_26_9'].iloc[-1]
            
            precio = df['close'].iloc[-1]
            distancia = ((precio - ema_val) / ema_val) * 100
            
            # --- REVISAR POSICIÓN ---
            posiciones = client.futures_position_information(symbol=symbol)
            datos_pos = next(p for p in posiciones if p['symbol'] == symbol)
            en_posicion = float(datos_pos['positionAmt']) != 0

            if not en_posicion:
                # ESTRATEGIA PARA SHORT (Venta)
                # Ahora requiere MACD Bajista (Línea < Señal)
                if adx_val > 26 and distancia < -9 and macd_line < macd_signal:
                    print(f"🔥 DISPARO SHORT: ADX {adx_val:.2f} | MACD OK | Dist {distancia:.2f}")
                    
                    balance = float(client.futures_account_balance()[1]['balance'])
                    cantidad = (balance * capital_percent * leverage) / precio
                    
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=round(cantidad, 3))
                    
                    # Trailing Stop ajustado al 0.5%
                    client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type='TRAILING_STOP_MARKET',
                        quantity=round(cantidad, 3),
                        callbackRate=0.5,
                        workingType='MARK_PRICE'
                    )
                    print("✅ SHORT ABIERTO - TRAILING 0.5%")

                # ESTRATEGIA PARA LONG (Compra)
                # Ahora requiere MACD Alcista (Línea > Señal)
                elif adx_val > 26 and distancia > 9 and macd_line > macd_signal:
                    print(f"🚀 DISPARO LONG: ADX {adx_val:.2f} | MACD OK | Dist {distancia:.2f}")
                    
                    balance = float(client.futures_account_balance()[1]['balance'])
                    cantidad = (balance * capital_percent * leverage) / precio
                    
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=round(cantidad, 3))
                    
                    client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type='TRAILING_STOP_MARKET',
                        quantity=round(cantidad, 3),
                        callbackRate=0.5,
                        workingType='MARK_PRICE'
                    )
                    print("✅ LONG ABIERTO - TRAILING 0.5%")

                else:
                    print(f"🔎 ETH: {precio} | ADX: {adx_val:.2f} | Dist: {distancia:.2f} | ESPERAR")
            
            else:
                print(f"🛡️ ALE2: POSICIÓN ACTIVA EN {precio} - MONITOREANDO")

            time.sleep(30) 

        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador()
