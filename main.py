import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# Intentamos importar Flask para el escudo anti-pausa
try:
    from flask import Flask
except ImportError:
    Flask = None

# --- ESCUDO ANTI-PAUSA ---
if Flask:
    app = Flask('')
    @app.route('/')
    def home():
        return "Gatito Quantum v11: Sistema Chajá Patrullando 24/7"
    def run_web():
        app.run(host='0.0.0.0', port=8080)

# ==========================================
# 🔱 CONFIGURACIÓN DE IDENTIDAD
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v11 - REAL"
API_KEY = 'TU_API_KEY_AQUI' 
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS ESTRATÉGICOS ---
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20 # Interés Compuesto (20%)
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    """Calcula indicadores y maneja errores de conexión"""
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        if not klines or len(klines) < 200:
            return None, None, None, None

        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])

        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p = df['close'].iloc[-1]
        d = abs(p - ema200)
        
        # ADX Matemático Real
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

        # Obtener capital actual para interés compuesto
        balance = client.futures_account_balance()
        capital_actual = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')

        return p, d, a, capital_actual
    except Exception as e:
        print(f"📡 Sincronizando... ({e})")
        sys.stdout.flush()
        return None, None, None, None

def ejecutar_orden(tipo, precio, capital):
    """Calcula la cantidad según el 20% y dispara a Binance"""
    try:
        # Lógica de Interés Compuesto
        margen = capital * PORCENTAJE_OP
        monto_con_leverage = margen * LEVERAGE
        cantidad_eth = round(monto_con_leverage / precio, 3)
        
        print(f"🔥 {tipo} DETECTADO. Margen: ${margen:.2f} | Comprando: {cantidad_eth} ETH")
        
        # --- ORDEN REAL (ACTIVA) ---
        orden = client.futures_create_order(
            symbol=SIMBOLO, 
            side='BUY', 
            type='MARKET', 
            quantity=cantidad_eth
        )
        print(f"✅ ORDEN EXITOSA: {orden['orderId']}")
        sys.stdout.flush()
        return True
    except Exception as e:
        print(f"❌ Error al ejecutar orden: {e}")
        sys.stdout.flush()
        return False

def main_loop():
    print(f"🚀 {NOMBRE_BOT} - COTO DE CAZA ABIERTO")
    sys.stdout.flush()
    while True:
        p, d, a, cap = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            print(f"💓 [{hora}] P: {p:.2f} | DIST: {d:.2f} | ADX: {a:.2f} | CAP: ${cap:.2f}")
            sys.stdout.flush()

            # Condición de entrada Ale
            if d >= DISTANCIA_MIN:
                if a >= ADX_CAZADORA:
                    tipo_msg = "🔱 HACHAZO" if a >= ADX_HACHAZO else "🎯 CAZADORA"
                    exito = ejecutar_orden(tipo_msg, p, cap)
                    if exito:
                        print("💤 Operación abierta. Durmiendo 30 min para dejar correr.")
                        time.sleep(1800)
            
        time.sleep(35)

if __name__ == "__main__":
    if Flask:
        t = Thread(target=run_web)
        t.daemon = True
        t.start()
    main_loop()
