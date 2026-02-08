import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- CONFIGURACIÓN DE SEGURIDAD ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

# --- ESCUDO ANTI-PAUSA ---
try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gladiador Sniper v12.2: Cazando Máximos"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS TÁCTICOS DE ÉLITE
# ==========================================
NOMBRE_BOT = "GLADIADOR SNIPER v12.2"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # 20% Capital (Interés Compuesto)
LEVERAGE = 10          
ADX_ENTRADA = 22.0     
ADX_SALIDA_BASE = 15.0 # Salida normal
ADX_SALIDA_SNIPER = 25.0 # Salida ajustada si hubo mucha fuerza
DISTANCIA_EMA = 5.0    
en_posicion = False      

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_actual = df['close'].iloc[-1]
        
        # CÁLCULO ADX Y DI (FUERZA REAL)
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        dx = 100 * abs(p_di - m_di) / (p_di + m_di)
        # Suavizado rápido para el ADX
        adx_val = dx # En v12.2 usamos el valor directo para máxima reacción
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_actual, p_di, m_di, adx_val, cap, ema200
    except Exception as e:
        print(f"📡 Sincronizando: {e}")
        return None, None, None, None, None, None

def cerrar_posicion(motivo):
    global en_posicion
    try:
        info = client.futures_position_information(symbol=SIMBOLO)
        cantidad = abs(float(next(p['positionAmt'] for p in info if p['symbol'] == SIMBOLO)))
        if cantidad > 0:
            client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=cantidad)
            print(f"💰 CIERRE SNIPER: {cantidad} ETH | Motivo: {motivo}")
            en_posicion = False
            return True
    except Exception as e:
        print(f"❌ Error al cerrar: {e}")
    return False

def main_loop():
    global en_posicion
    print(f"🚀 {NOMBRE_BOT} - ACTIVADO")
    
    # Detección inicial
    try:
        pos = client.futures_position_information(symbol=SIMBOLO)
        if abs(float(next(p['positionAmt'] for p in pos if p['symbol'] == SIMBOLO))) > 0:
            en_posicion = True
            print("🎯 Detectada posición abierta. Entrando en modo VIGILANCIA.")
    except: pass

    while True:
        p, p_di, m_di, adx, cap, ema = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            fuerza = "🐂" if p_di > m_di else "🐻"
            distancia = p - ema
            
            if not en_posicion:
                print(f"🔎 [{hora}] {fuerza} | ADX: {adx:.1f} | P: {p:.1f} | EMA: {ema:.1f}")
                # Entrada: Precio arriba de EMA + Distancia + Fuerza ADX
                if p > ema and distancia >= DISTANCIA_EMA and adx >= ADX_ENTRADA:
                    margen = cap * PORCENTAJE_OP
                    cantidad = round((margen * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad)
                    print(f"🔥 ENTRADA: {cantidad} ETH a {p}")
                    en_posicion = True
            
            else:
                # MODO SNIPER (Vigilancia de Ganancia Máxima)
                # Si el ADX fue muy alto (ej. el 34.7 que viste), subimos el piso de salida
                umbral_salida = ADX_SALIDA_SNIPER if adx > 30 else ADX_SALIDA_BASE
                
                print(f"👀 [{hora}] {fuerza} | P: {p:.1f} | ADX: {adx:.1f} | Piso Salida: {umbral_salida}")
                
                # Reglas de Salida de Élite
                if adx < umbral_salida:
                    cerrar_posicion(f"Agotamiento de Fuerza ({adx:.1f})")
                elif p < (ema * 0.998): # Colchón del 0.2%
                    cerrar_posicion("Ruptura de Tendencia (EMA)")
                elif m_di > p_di and adx > 35: # Cruce bajista con mucha fuerza
                    cerrar_posicion("Hachazo Sniper: Cambio de dirección detectado")
            
            sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    if app:
        Thread(target=run_web, daemon=True).start()
    main_loop()
