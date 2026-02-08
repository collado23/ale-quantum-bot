import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from threading import Thread

# --- CONFIGURACIÓN DE ENTORNO ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gladiador v12.9 Quantum: 500 Velas + 500 Puntas"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except Exception:
    app = None

# ==========================================
# 🔱 CONFIGURACIÓN TÁCTICA QUANTUM
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   
LEVERAGE = 10          
FILTRO_DI = 12.0       
ADX_MINIMO = 25.0      
DISTANCIA_EMA = 2.0    

client = Client(API_KEY, SECRET_KEY)

def obtener_datos_quantum_full():
    try:
        # 1. 🛡️ VISIÓN DE 500 VELAS (Memoria de largo plazo)
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        # EMA 200 calculada sobre las 500 velas
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # DMI / ADX con base de datos de 500 periodos
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx_val = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        # 2. 🛡️ ANÁLISIS DE LIBRO (500 PUNTAS)
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        vol_compras = sum(float(bid[1]) for bid in depth['bids']) 
        vol_ventas = sum(float(ask[1]) for ask in depth['asks'])  
        
        # 3. Capital (Interés Compuesto)
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema, vol_compras, vol_ventas
        
    except Exception as e:
        print(f"📡 Error en lectura de 500: {e}")
        return None, None, None, None, None, None, None, None

def main_loop():
    print(f"🚀 {SIMBOLO} | 500 VELAS | 500 PUNTAS | v12.9")
    
    while True:
        p, p_di, m_di, adx, cap, ema, v_comp, v_vent = obtener_datos_quantum_full()
        
        if p is not None:
            try:
                pos_info = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos_info if i['symbol'] == SIMBOLO)
                
                if amt == 0:
                    diff_di = abs(p_di - m_di)
                    print(f"🔎 P:{p:.1f} | EMA200:{ema:.1f} | VentajaDI:{diff_di:.1f} | L-Com:{v_comp:.0f}")
                    
                    # Filtros Quantum: EMA + DMI + ADX + Libro de Órdenes
                    if p > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                        print(f"🔥 LONG: 500 Velas y Libro Confirman.")
                    
                    elif p < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                        print(f"📉 SHORT: 500 Velas y Libro Confirman.")
                
                else:
                    # El Hachazo se mantiene intacto
                    if (amt > 0 and p < ema) or (amt < 0 and p > ema):
                        side_c = 'SELL' if amt > 0 else 'BUY'
                        client.futures_create_order(symbol=SIMBOLO, side=side_c, type='MARKET', quantity=abs(amt))
                        print(f"🛑 HACHAZO: Salida por cruce de EMA 200.")
                    
                    elif (amt > 0 and m_di > p_di) or (amt < 0 and p_di > m_di):
                        side_c = 'SELL' if amt > 0 else 'BUY'
                        client.futures_create_order(symbol=SIMBOLO, side=side_c, type='MARKET', quantity=abs(amt))
                        print(f"⚠️ CIERRE: Pérdida de fuerza en indicadores.")

            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            sys.stdout.flush()
        time.sleep(15)

if __name__ == "__main__":
    if app: Thread(target=run_web, daemon=True).start()
    main_loop()
