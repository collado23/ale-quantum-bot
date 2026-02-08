import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- CONEXIÓN CON VARIABLES DE RAILWAY ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

# Intentamos importar Flask para el escudo anti-pausa
try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home():
        return "Gatito Quantum v12: Gladiador Activo"
    def run_web():
        app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS ESTRATÉGICOS
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v12 - GLADIADOR"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20  # Interés Compuesto
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_CAZADORA = 19.0
ADX_AGOTAMIENTO = 17.5  # Nivel donde la fuerza se apaga
en_posicion = False      # Estado inicial del bot

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        if not klines or len(klines) < 200:
            return None, None, None, None, None

        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])

        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p = df['close'].iloc[-1]
        d = abs(p - ema200)
        
        # ADX Real Ale
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

        # Balance para Interés Compuesto
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')

        return p, d, a, cap, ema200
    except Exception as e:
        print(f"📡 Error sincronizando datos: {e}")
        sys.stdout.flush()
        return None, None, None, None, None

def cerrar_posicion():
    global en_posicion
    try:
        # Consultar posición real en Binance
        info = client.futures_position_information(symbol=SIMBOLO)
        cantidad_actual = abs(float(next(p['positionAmt'] for p in info if p['symbol'] == SIMBOLO)))
        
        if cantidad_actual > 0:
            # Orden de venta para cerrar el Long
            client.futures_create_order(
                symbol=SIMBOLO,
                side='SELL',
                type='MARKET',
                quantity=cantidad_actual
            )
            print(f"💰 CIERRE DE POSICIÓN: {cantidad_actual} ETH vendidos por agotamiento.")
            en_posicion = False
            return True
    except Exception as e:
        print(f"❌ Error al intentar cerrar: {e}")
    return False

def main_loop():
    global en_posicion
    print(f"🚀 {NOMBRE_BOT} - INICIADO")
    sys.stdout.flush()
    
    while True:
        p, d, a, cap, ema = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            
            if not en_posicion:
                # MODO BÚSQUEDA
                print(f"🔎 [{hora}] BUSCANDO | P: {p:.2f} | ADX: {a:.2f} | CAP: ${cap:.2f}")
                sys.stdout.flush()
                
                if d >= DISTANCIA_MIN and a >= ADX_CAZADORA:
                    margen = cap * PORCENTAJE_OP
                    cantidad = round((margen * LEVERAGE) / p, 3)
                    
                    try:
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad)
                        print(f"🔥 ENTRADA REALIZADA: {cantidad} ETH")
                        en_posicion = True
                    except Exception as e:
                        print(f"❌ Error al comprar: {e}")
            
            else:
                # MODO VIGILANCIA (Adentro de la operación)
                print(f"👀 [{hora}] VIGILANDO | P: {p:.2f} | ADX: {a:.2f} | EMA: {ema:.2f}")
                sys.stdout.flush()
                
                # CIERRE POR AGOTAMIENTO O RUPTURA DE TENDENCIA
                # 
                if a < ADX_AGOTAMIENTO:
                    print("⚠️ Agotamiento de fuerza (ADX bajo 17.5).")
                    cerrar_posicion()
                    time.sleep(600) # Descanso de 10 min tras cerrar
                
                elif p < ema:
                    print("⚠️ Ruptura de tendencia (Precio bajo EMA 200).")
                    cerrar_posicion()
                    time.sleep(600)

        time.sleep(30)

if __name__ == "__main__":
    if app:
        t = Thread(target=run_web)
        t.daemon = True
        t.start()
    main_loop()
