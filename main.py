import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# ==========================================
# 🔱 CONFIGURACIÓN DE IDENTIDAD Y SEGURIDAD
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v6 GOLD"
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS TÉCNICOS (Tus Reglas) ---
SIMBOLO = 'ETHUSDT'
CAPITAL_TOTAL = 36.02       # Capital inicial detectado
PORCENTAJE_OP = 0.20        # 20% Interés Compuesto
LEVERAGE = 10               # x10 siempre
DISTANCIA_MIN = 5.0         # Filtro de seguridad
ADX_HACHAZO = 24.0          # Señal de Poder
ADX_CAZADORA = 19.0         # Señal Rápida

# Inicializar conexión con Binance
client = Client(API_KEY, SECRET_KEY)

# ==========================================
# 🔱 MOTOR DE CÁLCULO (El Cerebro)
# ==========================================

def obtener_datos_mercado():
    """Trae velas reales y calcula EMA y ADX"""
    try:
        # Pedimos las últimas 100 velas de 5 minutos
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','qv','nt','tb','tbb','i'])
        
        # Convertir a números
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # 1. Calcular EMA 200
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        precio_actual = df['close'].iloc[-1]
        
        # 2. Calcular Distancia
        distancia = abs(precio_actual - ema200)

        # 3. Calcular ADX (Fuerza real)
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
        adx_final = dx.rolling(window=14).mean().iloc[-1]

        return precio_actual, distancia, adx_final

    except Exception as e:
        print(f"⚠️ Error en lectura de datos: {e}")
        return None, None, None

def latido_quantum(p, d, a):
    """Mantiene el log activo y evita el 'Stopping Container'"""
    hora = time.strftime('%H:%M:%S')
    print(f"💓 [LATIDO {hora}] P: {p} | DIST: {d:.2f} | ADX: {a:.2f}")
    sys.stdout.flush() # Obliga a Railway a registrar actividad

def abrir_operacion(tipo_señal, saldo):
    """Calcula el margen del 20% y ejecuta la orden x10"""
    margen = saldo * PORCENTAJE_OP
    total_posicion = margen * LEVERAGE
    
    print(f"🔥 {tipo_señal} DETECTADA")
    print(f"✅ Ejecutando: Margen ${margen:.2f} | Posición Total: ${total_posicion:.2f}")
    
    try:
        # Aquí iría la orden real (Descomentar para usar)
        # client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=...)
        pass
    except Exception as e:
        print(f"❌ Error al ejecutar en Binance: {e}")

# ==========================================
# 🔱 BUCLE PRINCIPAL (Vigilancia 24/7)
# ==========================================

def main():
    print(f"🚀 {NOMBRE_BOT} - SISTEMA CHAJÁ INICIADO")
    print(f"💰 Operando con capital de: ${CAPITAL_TOTAL}")
    
    operacion_abierta = False

    while True:
        # 1. Obtener indicadores reales
        precio, dist, adx = obtener_datos_mercado()
        
        if precio is not None:
            # 2. Latido de seguridad
            latido_quantum(precio, dist, adx)
            
            # 3. Lógica de decisión Ale (Dual 19/24)
            if not operacion_abierta:
                if dist >= DISTANCIA_MIN:
                    if adx >= ADX_HACHAZO:
                        abrir_operacion("🔱 HACHAZO SEGURO (ADX 24)", CAPITAL_TOTAL)
                        operacion_abierta = True # Evita duplicar órdenes
                    elif adx >= ADX_CAZADORA:
                        abrir_operacion("🎯 ENTRADA CAZADORA (ADX 19)", CAPITAL_TOTAL)
                        operacion_abierta = True
            
        # Esperar 30 segundos antes de la próxima lectura
        time.sleep(30)

if __name__ == "__main__":
    main()
