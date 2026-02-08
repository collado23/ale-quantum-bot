import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- IMPORTACIÓN DE TUS LLAVES (Desde Ale2.py) ---
try:
    import Ale2
    API_KEY = Ale2.API_KEY.strip()
    SECRET_KEY = Ale2.SECRET_KEY.strip()
    print("✅ Llaves cargadas correctamente desde Ale2")
except Exception as e:
    print(f"❌ Error al leer Ale2.py: {e}")
    # Si falla la importación, el bot no arranca por seguridad
    sys.exit()

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
        return "Gatito Quantum v11: Sistema Chajá con Conexión Ale2"
    def run_web():
        app.run(host='0.0.0.0', port=8080)

# ==========================================
# 🔱 PARÁMETROS ESTRATÉGICOS
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v11 - REAL"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20  # Interés Compuesto
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    """Trae datos y el capital real para Interés Compuesto"""
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
        a = dx.rolling(window=14).mean().iloc[-1]

        # Interés Compuesto: Leer balance real de Binance
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')

        return p, d, a, cap
    except Exception as e:
        print(f"📡 Sincronizando con Binance... ({e})")
        sys.stdout.flush()
        return None, None, None, None

def ejecutar_orden(tipo, precio, capital):
    try:
        # Cálculo del 20% del capital real
        margen = capital * PORCENTAJE_OP
        monto_con_leverage = margen * LEVERAGE
        cantidad_eth = round(monto_con_leverage / precio, 3)
        
        print(f"🔥 {tipo} DETECTADO. Margen: ${margen:.2f} | Comprando: {cantidad_eth} ETH")
        
        # --- ORDEN REAL ACTIVA ---
        orden = client.futures_create_order(
            symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad_eth
        )
        print(f"✅ ORDEN EXITOSA ID: {orden['orderId']}")
        sys.stdout.flush()
        return True
    except Exception as e:
        print(f"❌ Error en Binance: {e}")
        sys.stdout.flush()
        return False

def main_loop():
    print(f"🚀 {NOMBRE_BOT} - COTO DE CAZA CONECTADO A ALE2")
    sys.stdout.flush()
    while True:
        p, d, a, cap = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            print(f"💓 [{hora}] P: {p:.2f} | DIST: {d:.2f} | ADX: {a:.2f} | CAP: ${cap:.2f}")
            sys.stdout.flush()

            if d >= DISTANCIA_MIN and a >= ADX_CAZADORA:
                tipo_msg = "🔱 HACHAZO" if a >= ADX_HACHAZO else "🎯 CAZADORA"
                exito = ejecutar_orden(tipo_msg, p, cap)
                if exito:
                    print("💤 Operación abierta. Pausa de 30 min para proteger capital.")
                    time.sleep(1800)
            
        time.sleep(35)

if __name__ == "__main__":
    if Flask:
        t = Thread(target=run_web)
        t.daemon = True
        t.start()
    main_loop()
