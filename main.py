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

# --- ESCUDO ANTI-PAUSA (FLASK) ---
try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gatito Quantum v12.1: Estratega en Guardia"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS ESTRATÉGICOS CALIBRADOS
# ==========================================
NOMBRE_BOT = "GATITO QUANTUM v12.1 - ESTRATEGA"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # Interés Compuesto (20%)
LEVERAGE = 10          # Apalancamiento fijo
DISTANCIA_MIN = 5.0    # Separación mínima de la EMA 200
ADX_CAZADORA = 22.0    # Entrada: Más exigente
ADX_AGOTAMIENTO = 15.0 # Salida: Más aire (antes 17.5)
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
        
        # EMA 200 (Nuestra Brújula)
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p = df['close'].iloc[-1]
        d = abs(p - ema200)
        
        # ADX Real Ale (Fuerza de Tendencia)
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
        
        # Capital para Interés Compuesto
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p, d, a, cap, ema200
    except Exception as e:
        print(f"📡 Sincronizando... {e}")
        return None, None, None, None, None

def cerrar_posicion():
    global en_posicion
    try:
        info = client.futures_position_information(symbol=SIMBOLO)
        cantidad = abs(float(next(p['positionAmt'] for p in info if p['symbol'] == SIMBOLO)))
        if cantidad > 0:
            client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=cantidad)
            print(f"💰 CIERRE EXITOSO: {cantidad} ETH liquidados.")
            en_posicion = False
            return True
    except Exception as e:
        print(f"❌ Error al cerrar: {e}")
    return False

def main_loop():
    global en_posicion
    print(f"🚀 {NOMBRE_BOT} - INICIADO")
    
    # --- ESCANEO DE ARRANQUE ---
    try:
        info = client.futures_position_information(symbol=SIMBOLO)
        pos_amt = float(next(p['positionAmt'] for p in info if p['symbol'] == SIMBOLO))
        if abs(pos_amt) > 0:
            en_posicion = True
            print(f"✅ POSICIÓN DETECTADA: {pos_amt} ETH. El Estratega toma el mando.")
    except: pass
    
    sys.stdout.flush()
    
    while True:
        p, d, a, cap, ema = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            
            if not en_posicion:
                # MODO BÚSQUEDA
                print(f"🔎 [{hora}] BUSCANDO | P: {p:.2f} | ADX: {a:.2f} (Necesita 22.0)")
                # Solo entra si el precio está ARRIBA de la EMA y ADX es fuerte
                if p > ema and d >= DISTANCIA_MIN and a >= ADX_CAZADORA:
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
                # SALIDA: Si ADX baja de 15 o precio cae 0.2% debajo de la EMA
                if a < ADX_AGOTAMIENTO or p < (ema * 0.998):
                    razon = "Agotamiento ADX" if a < ADX_AGOTAMIENTO else "Ruptura EMA (Colchón 0.2%)"
                    print(f"⚠️ SEÑAL DE SALIDA: {razon}")
                    cerrar_posicion()
                    time.sleep(600) # Descanso de 10 min
            
            sys.stdout.flush()
        
        time.sleep(30) # Escaneo cada 30 segundos

if __name__ == "__main__":
    if app:
        t = Thread(target=run_web, daemon=True)
        t.start()
    main_loop()
