import os
import time
import pandas as pd
import numpy as np
from binance.client import Client
from binance.enums import *

# --- CONEXIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = 'ETHUSDT'
leverage = 10
capital_percent = 0.20 

def calcular_adx(df, length=14):
    df = df.copy()
    df['h-l'] = df['high'] - df['low']
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    tr_smooth = df['tr'].ewm(alpha=1/length, adjust=False).mean()
    df['up'] = df['high'] - df['high'].shift(1)
    df['down'] = df['low'].shift(1) - df['low']
    df['+dm'] = np.where((df['up'] > df['down']) & (df['up'] > 0), df['up'], 0)
    df['-dm'] = np.where((df['down'] > df['up']) & (df['down'] > 0), df['down'], 0)
    plus_di = 100 * (df['+dm'].ewm(alpha=1/length, adjust=False).mean() / tr_smooth)
    minus_di = 100 * (df['-dm'].ewm(alpha=1/length, adjust=False).mean() / tr_smooth)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/length, adjust=False).mean()
    return adx.iloc[-1]

def ejecutar_gladiador():
    print(f"🔱 ALE2.py COMPLETO - MONITOREANDO {symbol}")
    
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except:
        pass

    while True:
        try:
            # DESCARGA DE DATOS
            klines = client.futures_klines(symbol=symbol, interval='5m', limit=150)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','q','n','tb','tq','i'])
            df[['high','low','close']] = df[['high','low','close']].astype(float)
            
            # CÁLCULOS
            precio = df['close'].iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            distancia = ((precio - ema_200) / ema_200) * 100
            adx_val = calcular_adx(df)
            
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_l = (ema12 - ema26).iloc[-1]
            macd_s = (ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1]

            # LOG DE ESTADO
            est_macd = "ALZA 🟢" if macd_l > macd_s else "BAJA 🔴"
            print(f"📊 ETH: {precio:.2f} | Dist: {distancia:.2f}% | ADX: {adx_val:.1f} | MACD: {est_macd}")

            # REVISAR POSICIÓN
            pos = client.futures_position_information(symbol=symbol)
            # Buscamos la posición específica del símbolo
            pos_act = next((p for p in pos if p['symbol'] == symbol), None)
            en_vuelo = float(pos_act['positionAmt']) != 0 if pos_act else False

            if not en_vuelo:
                # ESTRATEGIA SHORT
                if adx_val > 26 and distancia < -9 and macd_l < macd_s:
                    balance = float(client.futures_account_balance()[1]['balance'])
                    qty = (balance * capital_percent * leverage) / precio
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=round(qty, 3))
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type='TRAILING_STOP_MARKET', quantity=round(qty, 3), callbackRate=0.5, workingType='MARK_PRICE')
                    print(f"🔥 DISPARO SHORT - ADX {adx_val:.1f} CONFIRMADO")

                # ESTRATEGIA LONG
                elif adx_val > 26 and distancia > 9 and macd_l > macd_s:
                    balance = float(client.futures_account_balance()[1]['balance'])
                    qty = (balance * capital_percent * leverage) / precio
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=round(qty, 3))
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type='TRAILING_STOP_MARKET', quantity=round(qty, 3), callbackRate=0.5, workingType='MARK_PRICE')
                    print(f"🚀 DISPARO LONG - ADX {adx_val:.1f} CONFIRMADO")
            else:
                # Si estamos en posición, solo monitoreamos sin intentar abrir otra
                pass

            time.sleep(30)

        except Exception as e:
            print(f"⚠️ Reintentando: {e}")
            time.sleep(20)

if __name__ == "__main__":
    ejecutar_gladiador()
