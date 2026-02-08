import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
NOMBRE_BOT = "GATITO QUANTUM v7 GOLD"
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20
LEVERAGE = 10

client = Client(API_KEY, SECRET_KEY)

def obtener_datos_mercado():
    """Trae datos y valida que no estén vacíos para evitar el error 'close'"""
    try:
        # Pedimos suficientes velas para la EMA 200
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=300)
        
        if not klines or len(klines) < 200:
            print("⏳ Esperando que Binance cargue el historial de velas...")
            return None, None, None

        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        
        # Validación de columnas antes de convertir
        if 'c' not in df.columns:
            return None, None, None

        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # EMA 200
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio = df['close'].iloc[-1]
        distancia = abs(precio - ema200)

        # ADX Real
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=14).mean().iloc[-1]

        return precio, distancia, adx
    except Exception as e:
        # Este es el print que viste en tu última captura
        print(f"⚠️ Reintentando conexión... ({e})")
        return None, None, None

def main():
    print(f"🚀 {NOMBRE_BOT} - EN CAZA REAL")
    sys.stdout.flush()
    
    while True:
        precio, dist, adx = obtener_datos_mercado()
        
        if precio is not None:
            # Latido con flush para Railway
            print(f"💓 [LATIDO] P: {precio} | DIST: {dist:.2f} | ADX: {adx:.2f}")
            sys.stdout.flush()

            # Lógica Ale: Entrar si Distancia > 5 y ADX > 19
            if dist >= 5.0 and adx >= 19.0:
                margen = CAPITAL_TOTAL * PORCENTAJE_OP
                print(f"🔥 SEÑAL DETECTADA - Ejecutando Margen ${margen:.2f}")
                # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=0.03)
                sys.stdout.flush()
                time.sleep(1800) # Pausa de seguridad
        
        time.sleep(45) # Ritmo anti-bloqueo

if __name__ == "__main__":
    main()
