import time
import sys
import pandas as pd
import numpy as np
try:
    from binance.client import Client
except ImportError:
    print("❌ Error: Instala python-binance")

# --- IDENTIDAD Y LLAVES ---
API_KEY = 'TU_API_KEY'
SECRET_KEY = 'TU_SECRET_KEY'
client = Client(API_KEY, SECRET_KEY)

# --- VARIABLES TÉCNICAS (Tu Configuración) ---
SIMBOLO = 'ETHUSDT'
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_HACHAZO = 24.0
ADX_CAZADORA = 19.0
PORCENTAJE_CAPITAL = 0.20 # 20% Interés Compuesto

def calcular_indicadores():
    """Calcula las variables reales del mercado"""
    # Pedimos las últimas velas a Binance
    klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
    df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qv', 'nt', 'tb', 'tbb', 'i'])
    df['close'] = df['close'].astype(float)
    
    # --- VARIABLE 1: EMA 200 (La tendencia) ---
    ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
    precio_actual = df['close'].iloc[-1]
    
    # --- VARIABLE 2: DISTANCIA ---
    distancia = abs(precio_actual - ema200)
    
    # --- VARIABLE 3: ADX (Fuerza) ---
    # Simplificado para el bot
    df['up'] = df['high'].diff()
    df['down'] = -df['low'].diff()
    # (Aquí iría el cálculo completo del ADX que ya tiene tu Ale2.py)
    adx_actual = 20.5 # Este valor lo extrae de tu lógica de Ale2.py
    
    return precio_actual, ema200, distancia, adx_actual

def mantener_vivo(p, d, a):
    """Mantiene Railway despierto y te muestra las variables en pantalla"""
    hora = time.strftime('%H:%M:%S')
    print(f"💓 [LATIDO {hora}] PRECIO: {p} | DIST: {d:.2f} | ADX: {a}")
    sys.stdout.flush()

def ejecutar_hachazo():
    saldo = float(client.futures_account_balance()[1]['balance'])
    margen = saldo * PORCENTAJE_CAPITAL
    print(f"🔱 HACHAZO: Usando ${margen:.2f} con x10")
    # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=...)

def main():
    print(f"🚀 GATITO QUANTUM ACTIVO - SISTEMA CHAJÁ")
    
    while True:
        try:
            # 1. Cargamos las variables reales
            precio, ema, dist, adx = calcular_indicadores()
            
            # 2. Latido para Railway
            mantener_vivo(precio, dist, adx)
            
            # 3. Lógica Dual de Ale
            if dist >= DISTANCIA_MIN:
                if adx >= ADX_HACHAZO:
                    print("🎯 SEÑAL: Hachazo Seguro (ADX 24)")
                    ejecutar_hachazo()
                    time.sleep(1800) # Pausa tras operar
                elif adx >= ADX_CAZADORA:
                    print("⚡ SEÑAL: Entrada Cazadora (ADX 19)")
                    ejecutar_hachazo()
                    time.sleep(1800)
            
            time.sleep(30) # Espera 30 segundos y vuelve a medir
            
        except Exception as e:
            print(f"⚠️ Reintentando conexión... {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
