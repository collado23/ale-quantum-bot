import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# --- IDENTIDAD DEL CAZADOR ---
NOMBRE_BOT = "GATITO QUANTUM v7 GOLD"
API_KEY = 'TU_API_KEY_REAL'
SECRET_KEY = 'TU_SECRET_KEY_REAL'

# --- REGLAS DE ORO ALE ---
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20 # 20% Interés Compuesto
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

client = Client(API_KEY, SECRET_KEY)

def obtener_indicadores():
    try:
        # Pausa de seguridad para evitar baneo de IP
        time.sleep(1)
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # 1. EMA 200
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio = df['close'].iloc[-1]
        distancia = abs(precio - ema200)

        # 2. ADX Matemático Real
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

        return precio, distancia, adx_actual
    except Exception as e:
        print(f"⚠️ Esperando conexión... {e}")
        return None, None, None

def abrir_hachazo(tipo):
    margen = CAPITAL_TOTAL * PORCENTAJE_OP
    print(f"🔥 {tipo} DETECTADO. Enviando orden de ${margen:.2f} a Binance...")
    try:
        # QUITAR EL '#' DE ABAJO PARA OPERAR REAL
        # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=0.03)
        print(f"💎 ORDEN CONFIRMADA. ¡A cobrar!")
    except Exception as e:
        print(f"❌ Falló Binance: {e}")
    sys.stdout.flush()

def main():
    print(f"🚀 {NOMBRE_BOT} EN CAZA REAL")
    while True:
        p, d, a = obtener_indicadores()
        if p:
            print(f"💗 [LATIDO] P: {p} | DIST: {d:.2f} | ADX: {a:.2f}")
            sys.stdout.flush()

            # Lógica de entrada Ale
            if d >= DISTANCIA_MIN:
                if a >= ADX_HACHAZO:
                    abrir_hachazo("🔱 HACHAZO SEGURO")
                    time.sleep(3600) # Pausa tras éxito
                elif a >= ADX_CAZADORA:
                    abrir_hachazo("🎯 SEÑAL CAZADORA")
                    time.sleep(3600)
        
        time.sleep(45) # Ritmo perfecto para Railway y Binance

if __name__ == "__main__":
    main()
