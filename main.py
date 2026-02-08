import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- VARIABLES DE ENTORNO RAILWAY ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

# --- ESCUDO ANTI-PAUSA ---
try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gatito Quantum v12: Gladiador en Guardia"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS ESTRATÉGICOS
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v12 - GLADIADOR"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20 
LEVERAGE = 10
DISTANCIA_MIN = 5.0
ADX_CAZADORA = 19.0
ADX_AGOTAMIENTO = 17.5 
en_posicion = False      

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        if not klines or len(klines) < 200: return None, None, None, None, None
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
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        a = dx.rolling(window=14).mean().iloc[-1]
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        return p, d, a, cap, ema200
    except Exception as e:
        print(f"📡 Error sincronización: {e}")
        return None, None, None, None, None

def cerrar_posicion():
    global en_posicion
    try:
        info = client.futures_position_information(symbol=SIMBOLO)
        cantidad_actual = abs(float(next(p['positionAmt'] for p in info if p['symbol'] == SIMBOLO)))
        if cantidad_actual > 0:
            client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=cantidad_actual)
            print(f"💰 CIERRE EXITOSO: {cantidad_actual} ETH liquidados.")
            en_posicion = False
            return True
    except Exception as e:
        print(f"❌ Error al cerrar: {e}")
    return False

def main_loop():
    global en_posicion
    print(f"🚀 {NOMBRE_BOT} - INICIADO")
    
    # --- ESCANEO DE ARRANQUE: HEREDAR POSICIÓN ---
    try:
        print("🔍 Escaneando posiciones abiertas en Binance...")
        info = client.futures_position_information(symbol=SIMBOLO)
        pos_amt = float(next(p['positionAmt'] for p in info if p['symbol'] == SIMBOLO))
        if abs(pos_amt) > 0:
            en_posicion = True
            print(f"✅ POSICIÓN DETECTADA: {pos_amt} ETH. El Gladiador toma el mando.")
        else:
            print("🌕 Sin posiciones previas. Buscando nuevas presas.")
    except Exception as e:
        print(f"⚠️ No se pudo escanear Binance al inicio: {e}")
    
    sys.stdout.flush()
    
    while True:
        p, d, a, cap, ema = obtener_datos()
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            if not en_posicion:
                print(f"🔎 [{hora}] BUSCANDO | P: {p:.2f} | ADX: {a:.2f} | CAP: ${cap:.2f}")
                if d >= DISTANCIA_MIN and a >= ADX_CAZADORA:
                    margen = cap * PORCENTAJE_OP
                    cantidad = round((margen * LEVERAGE) / p, 3)
                    try:
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad)
                        print(f"🔥 ENTRADA REALIZADA: {cantidad} ETH")
                        en_posicion = True
                    except Exception as e: print(f"❌ Error compra: {e}")
            else:
                # MODO VIGILANCIA
                print(f"👀 [{hora}] VIGILANDO | P: {p:.2f} | ADX: {a:.2f} | EMA: {ema:.2f}")
                if a < ADX_AGOTAMIENTO or p < ema:
                    print(f"⚠️ Señal de salida detectada (ADX: {a:.2f} | EMA: {ema:.2f})")
                    cerrar_posicion()
                    time.sleep(600)
            sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    if app:
        t = Thread(target=run_web); t.daemon = True; t.start()
    main_loop()
