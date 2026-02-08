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
    def home(): return "Gladiador v12.7: Operando"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except:
    app = None

# ==========================================
# 🔱 CONFIGURACIÓN TÁCTICA v12.7
# ==========================================
NOMBRE_BOT = "GLADIADOR v12.7"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.15   
LEVERAGE = 10          
DISTANCIA_EMA = 1.5    

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # ADX Robusto
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
        atr = tr.rolling(14).mean()
        p_di = 100 * (plus_dm.rolling(14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(14).mean() / atr).iloc[-1]
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, cap, ema
    except Exception as e:
        print(f"📡 Error datos: {e}")
        return None, None, None, None, None

def main_loop():
    print(f"🚀 {NOMBRE_BOT} - SISTEMA ESTABILIZADO")
    
    while True:
        p, p_di, m_di, cap, ema = obtener_datos()
        
        if p:
            try:
                # REVISIÓN DE POSICIÓN SEGURA
                pos_info = client.futures_position_information(symbol=SIMBOLO)
                # Buscamos la posición sin que explote si no hay nada
                amt = 0
                for item in pos_info:
                    if item['symbol'] == SIMBOLO:
                        amt = float(item['positionAmt'])
                        break
                
                if amt == 0:
                    print(f"🔎 Buscando... P: {p:.1f} | EMA: {ema:.1f} | DI+: {p_di:.1f} | DI-: {m_di:.1f}")
                    
                    # ENTRADA SHORT (M-DI gana por mucho y precio abajo de EMA)
                    if p < (ema - DISTANCIA_EMA) and m_di > (p_di + 8):
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                        print(f"📉 GATILLANDO SHORT - El mercado cae")
                    
                    # ENTRADA LONG (P-DI gana por mucho y precio arriba de EMA)
                    elif p > (ema + DISTANCIA_EMA) and p_di > (m_di + 8):
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                        print(f"🔥 GATILLANDO LONG - El mercado sube")
                
                else:
                    # GESTIÓN DE SALIDA (Si el precio cruza la EMA, cerramos para proteger)
                    # Si es Long y el precio cae de la EMA, o si es Short y el precio sube de la EMA
                    if (amt > 0 and p < ema) or (amt < 0 and p > ema):
                        side_cierre = 'SELL' if amt > 0 else 'BUY'
                        client.futures_create_order(symbol=SIMBOLO, side=side_cierre, type='MARKET', quantity=abs(amt))
                        print(f"🛑 PROTECCIÓN ACTIVADA: Posición cerrada por cruce de EMA")
            
            except Exception as e:
                print(f"⚠️ Error en loop: {e}")
            
            sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    if app: Thread(target=run_web, daemon=True).start()
    main_loop()
