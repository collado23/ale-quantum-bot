import os
import time
import pandas as pd
from binance.client import Client
from binance.enums import *

# CONEXIÓN USANDO TUS VARIABLES DE RAILWAY
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    print("❌ ERROR: LAS API KEYS SIGUEN VACÍAS EN RAILWAY")
else:
    print("✅ API KEYS ENCONTRADAS. CONECTANDO...")

client = Client(api_key, api_secret)
symbol = 'ETHUSDT'

def ejecutar():
    print(f"🔱 GLADIADOR ALE2 - MODO ESTABLE ACTIVO")
    while True:
        try:
            # Obtener datos y calcular MACD manual para evitar errores de librerías
            klines = client.futures_klines(symbol=symbol, interval='5m', limit=100)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','q','n','tb','tq','i'])
            close = df['c'].astype(float)
            
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            
            precio = close.iloc[-1]
            print(f"🔎 MONITOR: {precio} | MACD: {macd.iloc[-1]:.4f} | SIGNAL: {signal.iloc[-1]:.4f}")
            
            # (Aquí va el resto de tu lógica de disparo que ya conocés)
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ ESPERANDO CONEXIÓN: {e}")
            time.sleep(20)

if __name__ == "__main__":
    ejecutar()
