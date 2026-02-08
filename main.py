import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN DE IDENTIDAD ---
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS ESTRATÉGICOS (Memoria Ale) ---
SIMBOLO = 'ETHUSDT'
CAPITAL_INICIAL = 36.02
APALANCAMIENTO = 10           # x10 constante
PORCENTAJE_OP = 0.20          # 20% Interés Compuesto
DISTANCIA_MIN_EMA = 5.0       # Filtro de seguridad
ADX_HACHAZO = 24.0            # Entrada de Poder
ADX_CAZADORA = 19.0           # Entrada de Acción Rápida

# Inicialización de Binance
client = Client(API_KEY, SECRET_KEY)

def obtener_datos_mercado():
    """Calcula las variables reales: EMA 200, Distancia y ADX"""
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','qv','nt','tb','tbb','i'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # 1. EMA 200
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio_actual = df['close'].iloc[-1]

        # 2. Distancia a la EMA
        distancia = abs(precio_actual - ema200)

        # 3. Cálculo de ADX (Fuerza de Tendencia)
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=14).mean().iloc[-1]

        return precio_actual, distancia, adx
    except Exception as e:
        print(f"⚠️ Error leyendo datos: {e}")
        return None, None, None

def latido_railway(p, d, a):
    """Mantiene el proceso vivo en Railway"""
    hora = time.strftime('%H:%M:%S')
    print(f"💓 [LATIDO {hora}] PRECIO: {p} | DIST: {d:.2f} | ADX: {a:.2f}")
    sys.stdout.flush()

def ejecutar_orden(tipo, saldo_actual):
    """Ejecuta la operación con el 20% del capital"""
    margen = saldo_actual * PORCENTAJE_OP
    cantidad_eth = (margen * APALANCAMIENTO) / 2500 # Aproximación por precio
    
    print(f"🔥 {tipo} DETECTADA")
    print(f"✅ Enviando orden a Binance: Margen ${margen:.2f} | x10")
    
    try:
        # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad_eth)
        pass
    except Exception as e:
        print(f"❌ Error en Binance: {e}")

def main():
    print(f"🚀 {NOMBRE_BOT} INICIADO")
    print(f"💰 Operando con ${CAPITAL_INICIAL} | Estrategia Dual Ale")
    
    while True:
        precio, dist, adx = obtener_datos_mercado()
        
        if precio:
            latido_railway(precio, dist, adx)
            
            # Lógica de Decisión Dual
            if dist >= DISTANCIA_MIN_EMA:
                if adx >= ADX_HACHAZO:
                    ejecutar_orden("🔱 HACHAZO SEGURO (ADX 24)", CAPITAL_INICIAL)
                    time.sleep(1200) # Pausa de 20 min tras operar
                elif adx >= ADX_CAZADORA:
                    ejecutar_orden("🎯 ENTRADA CAZADORA (ADX 19)", CAPITAL_INICIAL)
                    time.sleep(1200)

        time.sleep(30) # Escaneo cada 30 segundos

if __name__ == "__main__":
    main()
