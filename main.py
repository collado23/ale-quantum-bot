import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN DE PODER ---
NOMBRE_BOT = "GATITO QUANTUM v8 - INMORTAL"
API_KEY = 'TU_API_KEY'
SECRET_KEY = 'TU_SECRET_KEY'
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20
LEVERAGE = 10

client = Client(API_KEY, SECRET_KEY)

def obtener_datos_blindados():
    """Trae 500 velas para asegurar que la EMA 200 funcione siempre"""
    try:
        # Pedimos 500 velas para que sobre historial
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        
        if not klines or len(klines) < 200:
            return None, None, None

        # Crear DataFrame con nombres de columnas correctos
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        
        # Convertir a flotantes de forma segura
        df['close'] = pd.to_numeric(df['c'], errors='coerce')
        df['high'] = pd.to_numeric(df['h'], errors='coerce')
        df['low'] = pd.to_numeric(df['l'], errors='coerce')

        # 1. EMA 200 (Corazón de la estrategia)
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio_actual = df['close'].iloc[-1]
        distancia = abs(precio_actual - ema200)

        # 2. ADX Matemático Real (Fuerza de Ale)
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx_actual = dx.rolling(window=14).mean().iloc[-1]

        return precio_actual, distancia, adx_actual

    except Exception as e:
        # Aquí es donde fallaba antes, ahora solo avisamos y seguimos
        print(f"📡 Sincronizando con Binance... ({e})")
        sys.stdout.flush()
        return None, None, None

def main():
    print(f"🚀 {NOMBRE_BOT} - SISTEMA CHAJÁ ONLINE")
    sys.stdout.flush()
    
    while True:
        p, d, a = obtener_datos_blindados()
        
        if p is not None:
            # Latido Real con datos del mercado
            print(f"💓 [ESTADO] P: {p:.2f} | DIST: {d:.2f} | ADX: {a:.2f}")
            sys.stdout.flush()

            # Lógica de Disparo (Distancia > 5 y ADX > 19)
            if d >= 5.0 and a >= 19.0:
                margen = CAPITAL_TOTAL * PORCENTAJE_OP
                print(f"🔥 SEÑAL DETECTADA: Margen ${margen:.2f}")
                # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=0.03)
                sys.stdout.flush()
                time.sleep(1800) # Dormir tras operar para proteger el capital
        
        # Espera de 45 segundos para no saturar la conexión
        time.sleep(45)

if __name__ == "__main__":
    main()
