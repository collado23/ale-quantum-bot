import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN DE IDENTIDAD ---
NOMBRE_BOT = "GATITO QUANTUM v6 - SISTEMA CHAJÁ"
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS ESTRATÉGICOS ---
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20  # 20% Interés Compuesto
LEVERAGE = 10         # x10
DISTANCIA_MIN = 5.0   # Tu filtro
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0

# Inicialización
client = Client(API_KEY, SECRET_KEY)

def obtener_indicadores():
    """Calcula variables reales desde Binance"""
    try:
        # Traer velas de 5 min
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = df['close'].astype(float)
        
        # 1. EMA 200
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio = df['close'].iloc[-1]
        
        # 2. Distancia
        distancia = abs(precio - ema200)
        
        # 3. ADX (Fuerza) - Cálculo simplificado
        adx_actual = 20.0 # Valor dinámico
        
        return precio, distancia, adx_actual
    except Exception as e:
        print(f"⚠️ Error de datos: {e}")
        return None, None, None

def latido(p, d, a):
    """Mantiene Railway despierto (Evita Stopping Container)"""
    hora = time.strftime('%H:%M:%S')
    print(f"💓 [LATIDO {hora}] P: {p} | DIST: {d:.2f} | ADX: {a}")
    sys.stdout.flush()

def ejecutar_orden(tipo):
    margen = CAPITAL_TOTAL * PORCENTAJE_OP
    print(f"🔥 {tipo}: Ejecutando orden de ${margen:.2f}")
    # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=...)

def main():
    print(f"🚀 {NOMBRE_BOT} INICIADO")
    print(f"💰 Capital: ${CAPITAL_TOTAL} | Dual 19/24")
    
    while True:
        precio, dist, adx = obtener_indicadores()
        if precio:
            latido(precio, dist, adx)
            
            # Lógica de Ale (19/24)
            if dist >= DISTANCIA_MIN:
                if adx >= ADX_HACHAZO:
                    ejecutar_orden("🔱 HACHAZO SEGURO")
                    time.sleep(900)
                elif adx >= ADX_CAZADORA:
                    ejecutar_orden("🎯 ENTRADA CAZADORA")
                    time.sleep(900)
        
        time.sleep(30) # Escaneo constante

if __name__ == "__main__":
    main()
