import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# ==========================================
# 🔱 CONFIGURACIÓN DE IDENTIDAD
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v9 - REACCIÓN"
API_KEY = 'TU_API_KEY_AQUI'  # <--- Poné tu llave entre las comillas
SECRET_KEY = 'TU_SECRET_KEY_AQUI' # <--- Poné tu llave secreta entre las comillas

# --- PARÁMETROS ESTRATÉGICOS ---
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

# Inicialización de conexión
client = Client(API_KEY, SECRET_KEY)

# ==========================================
# 🔱 MOTOR DE CÁLCULO Y CONEXIÓN
# ==========================================

def obtener_datos():
    """Trae datos de Binance y calcula EMA y ADX"""
    try:
        print("📡 Solicitando velas a Binance...") 
        sys.stdout.flush()
        
        # Pedimos 500 velas para que la EMA 200 sea ultra precisa
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        
        if not klines or len(klines) < 200:
            print(f"⏳ Historial insuficiente ({len(klines)} velas). Reintentando...")
            return None, None, None

        # Estructura de datos
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])

        # 1. Cálculo de EMA 200
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p = df['close'].iloc[-1]
        d = abs(p - ema200)
        
        # 2. Cálculo de ADX (Lógica Ale)
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
        print(f"⚠️ Error de conexión: {e}")
        sys.stdout.flush()
        return None, None, None

# ==========================================
# 🔱 BUCLE DE OPERACIÓN (Vigilancia 24/7)
# ==========================================

def main():
    print(f"🚀 {NOMBRE_BOT} ARRANCANDO...")
    sys.stdout.flush()
    
    while True:
        # 1. Obtener precio, distancia y ADX
        p, d, a = obtener_datos()
        
        if p is not None:
            # 2. Latido para Railway (con hora)
            hora = time.strftime('%H:%M:%S')
            print(f"💓 [{hora}] P: {p:.2f} | DIST: {d:.2f} | ADX: {a:.2f}")
            sys.stdout.flush()

            # 3. Lógica de disparo Ale
            if d >= DISTANCIA_MIN:
                if a >= ADX_HACHAZO:
                    print(f"🔱 HACHAZO SEGURO DETECTADO (ADX {a:.2f})")
                    # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=0.03)
                    sys.stdout.flush()
                    time.sleep(1800) # Pausa tras éxito
                elif a >= ADX_CAZADORA:
                    print(f"🎯 SEÑAL CAZADORA DETECTADA (ADX {a:.2f})")
                    # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=0.03)
                    sys.stdout.flush()
                    time.sleep(1800)
        
        # 4. Pausa de ciclo
        print("💤 Esperando 30 segundos para el próximo escaneo...")
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    main()
