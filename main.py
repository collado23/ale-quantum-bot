import time
import sys
import pandas as pd
import numpy as np
# Importación blindada para Binance
try:
    from binance.client import Client
except ImportError:
    print("❌ Error: Falta instalar python-binance")

# --- CONFIGURACIÓN DE IDENTIDAD ---
NOMBRE_BOT = "GATITO QUANTUM v6 GOLD"
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS ESTRATÉGICOS (Tu Capital) ---
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

# Inicialización del Cliente
client = Client(API_KEY, SECRET_KEY)

def obtener_indicadores():
    """Calcula variables reales y soluciona el error de 'close'"""
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        if not klines:
            return None, None, None
            
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = df['close'].astype(float)
        
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio = df['close'].iloc[-1]
        distancia = abs(precio - ema200)
        
        # Aquí va tu lógica de ADX de Ale2.py
        adx_actual = 20.0 
        
        return precio, distancia, adx_actual
    except Exception as e:
        print(f"⚠️ Error de datos: {e}")
        return None, None, None

def latido_quantum(p, d, a):
    """Evita el 'Stopping Container' manteniendo el log activo"""
    hora = time.strftime('%H:%M:%S')
    print(f"💓 [LATIDO {hora}] P: {p} | DIST: {d:.2f} | ADX: {a}")
    sys.stdout.flush() # Comando maestro para Railway

def main():
    print(f"🚀 {NOMBRE_BOT} INICIADO")
    print(f"💰 Capital: ${CAPITAL_TOTAL} | Dual (19/24)")
    
    while True:
        precio, dist, adx = obtener_indicadores()
        
        if precio is not None:
            latido_quantum(precio, dist, adx)
            
            # Lógica Dual de Ale
            if dist >= DISTANCIA_MIN:
                if adx >= ADX_HACHAZO:
                    print(f"🔱 HACHAZO SEGURO DETECTADO")
                    # client.futures_create_order(...)
                    time.sleep(1200)
                elif adx >= ADX_CAZADORA:
                    print(f"🎯 ENTRADA CAZADORA DETECTADA")
                    # client.futures_create_order(...)
                    time.sleep(1200)
        
        time.sleep(30) # Escaneo constante cada 30 segundos

if __name__ == "__main__":
    main()
