import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# --- ANTI-PAUSA: Servidor Web Auxiliar ---
app = Flask('')
@app.route('/')
def home():
    return "Gatito Quantum está despierto y patrullando 24/7"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# 🔱 CONFIGURACIÓN DE IDENTIDAD
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v10 - INMORTAL"
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS ---
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        if not klines or len(klines) < 200:
            return None, None, None

        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])

        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p = df['close'].iloc[-1]
        d = abs(p - ema200)
        
        # ADX Ale
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        a = dx.rolling(window=14).mean().iloc[-1]

        return p, d, a
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None, None, None

def main_loop():
    print(f"🚀 {NOMBRE_BOT} INICIADO")
    while True:
        p, d, a = obtener_datos()
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            print(f"💓 [{hora}] P: {p:.2f} | DIST: {d:.2f} | ADX: {a:.2f}")
            sys.stdout.flush()

            if d >= DISTANCIA_MIN:
                if a >= ADX_HACHAZO:
                    print("🔱 HACHAZO DETECTADO")
                    client.futures_create_order(...)
                elif a >= ADX_CAZADORA:
                    print("🎯 CAZADORA DETECTADA")
            
        time.sleep(30)

if __name__ == "__main__":
    # Iniciamos el servidor web en un hilo separado (Mantiene vivo el bot)
    t = Thread(target=run_web)
    t.start()
    # Iniciamos el bot real
    main_loop()
