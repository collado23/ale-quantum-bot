import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from threading import Thread
from flask import Flask

# --- ESCUDO ANTI-CAÍDAS RAILWAY ---
app = Flask('')
@app.route('/')
def home(): return "🛡️ Gladiador v12.9 Tanque: Activo"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONEXIÓN SEGURA ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')
client = Client(API_KEY, SECRET_KEY)

# ==========================================
# 🔱 CONFIGURACIÓN SUPREMA
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   
LEVERAGE = 10          
FILTRO_DI = 12.0       # <--- Tu barrera de seguridad
ADX_MINIMO = 25.0      
DISTANCIA_EMA = 2.0    

def obtener_datos_quantum_full():
    try:
        # 🛡️ MEMORIA DE 500 VELAS (Precisión absoluta)
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # DMI / ADX 
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx_val = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        # 🛡️ PROFUNDIDAD DE 500 PUNTAS (Libro de Órdenes)
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        vol_compras = sum(float(bid[1]) for bid in depth['bids']) 
        vol_ventas = sum(float(ask[1]) for ask in depth['asks'])  
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema, vol_compras, vol_ventas
    except Exception as e:
        print(f"📡 Reconectando... {e}")
        time.sleep(5)
        return None, None, None, None, None, None, None, None

def main_loop():
    print(f"🔱 GLADIADOR v12.9 - MODO TANQUE ACTIVADO")
    while True:
        p, p_di, m_di, adx, cap, ema, v_comp, v_vent = obtener_datos_quantum_full()
        
        if p is not None:
            try:
                pos = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                
                if amt == 0:
                    diff_di = abs(p_di - m_di)
                    print(f"🔎 Analizando: P:{p:.1f} | VentajaDI:{diff_di:.1f} | Libro-C:{v_comp:.0f}")
                    
                    # LÓGICA DE GATILLO CON CONFIRMACIÓN DE LIBRO
                    if p > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                        print(f"🔥 ATAQUE LONG: El libro y la tendencia confirman.")
                    
                    elif p < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                        print(f"📉 ATAQUE SHORT: El libro y la tendencia confirman.")
                
                else:
                    # SALIDA TÉCNICA (Hachazo + Debilidad)
                    if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                        side_c = 'SELL' if amt > 0 else 'BUY'
                        client.futures_create_order(symbol=SIMBOLO, side=side_c, type='MARKET', quantity=abs(amt))
                        print(f"🛑 CIERRE TÁCTICO: Protegiendo los {cap:.2f} USDT.")

            except BinanceAPIException as e: print(f"⚠️ Error Binance: {e}")
            except Exception as e: print(f"⚠️ Error: {e}")
            sys.stdout.flush()
        time.sleep(15)

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    main_loop()
