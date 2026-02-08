import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- SEGURIDAD ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gladiador v12.6: Operando"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except:
    app = None

# ==========================================
# 🔱 CONFIGURACIÓN TÁCTICA v12.6
# ==========================================
NOMBRE_BOT = "GLADIADOR v12.6"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.15   # Bajamos al 15% para mayor seguridad
LEVERAGE = 10          
ADX_ENTRADA = 25.0     
ADX_SALIDA = 20.0      
DISTANCIA_EMA = 2.0    

client = Client(API_KEY, SECRET_KEY)

def cerrar_todo_ahora():
    """Esta función limpia tu cuenta de cualquier operación abierta al arrancar"""
    try:
        pos = client.futures_position_information(symbol=SIMBOLO)
        for p in pos:
            amt = float(p['positionAmt'])
            if amt != 0:
                side = 'SELL' if amt > 0 else 'BUY'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=abs(amt))
                print(f"✅ LIMPIEZA INICIAL: Posición cerrada.")
    except Exception as e:
        print(f"⚠️ Sin posiciones para limpiar: {e}")

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # ADX Simple y Robusto
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
        atr = tr.rolling(14).mean()
        p_di = 100 * (plus_dm.rolling(14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(14).mean() / atr).iloc[-1]
        dx = 100 * abs(p_di - m_di) / (p_di + m_di)
        adx_val = dx # Simplificado para evitar errores de rolling
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema
    except:
        return None, None, None, None, None, None

def main_loop():
    print(f"🚀 {NOMBRE_BOT} - ACTIVADO")
    cerrar_todo_ahora() # <--- PRIMERO LIMPIAMOS LA CUENTA
    
    while True:
        p, p_di, m_di, adx, cap, ema = obtener_datos()
        
        if p:
            # Consultar si hay posición abierta
            pos_info = client.futures_position_information(symbol=SIMBOLO)
            pos_act = next(pa for pa in pos_info if pa['symbol'] == SIMBOLO)
            amt = float(pos_act['positionAmt'])
            
            if amt == 0:
                print(f"🔎 Buscando... P: {p:.1f} | EMA: {ema:.1f} | ADX: {p_di-m_di:.1f}")
                # ENTRADA SHORT (A LA BAJA) - Si el precio está abajo de la EMA
                if p < (ema - DISTANCIA_EMA) and m_di > (p_di + 7):
                    qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                    print(f"📉 ENTRANDO EN SHORT")
                # ENTRADA LONG (A LA SUBA)
                elif p > (ema + DISTANCIA_EMA) and p_di > (m_di + 7):
                    qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                    print(f"🔥 ENTRANDO EN LONG")
            else:
                # GESTIÓN DE SALIDA DE EMERGENCIA
                if (amt > 0 and p < ema) or (amt < 0 and p > ema):
                    cerrar_todo_ahora()
                    print(f"🛑 SALIDA POR CRUCE DE EMA")
            
            sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    if app: Thread(target=run_web, daemon=True).start()
    main_loop()
