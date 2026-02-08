import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. SERVIDOR DE VIDA INMEDIATA
# ==========================================
app = Flask('')

@app.route('/')
def health():
    return "Gladiador 12.9.4 Online", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Arrancar servidor inmediatamente para que Railway esté feliz
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🛡️ 2. MOTOR RESILIENTE
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   
LEVERAGE = 10          
FILTRO_DI = 12.0       
ADX_MINIMO = 25.0      
DISTANCIA_EMA = 2.0    

def conectar_binance():
    """Intenta conectar a Binance hasta lograrlo"""
    while True:
        try:
            api = os.getenv('API_KEY')
            sec = os.getenv('API_SECRET')
            if not api or not sec:
                print("⚠️ Esperando variables de entorno API...")
                time.sleep(5)
                continue
            
            c = Client(api, sec)
            # Prueba de conexión simple
            c.futures_account_balance()
            print("✅ Conexión con Binance establecida.")
            return c
        except Exception as e:
            print(f"📡 Error de conexión inicial: {e}. Reintentando en 10s...")
            time.sleep(10)

# Inicializar cliente
client = conectar_binance()

def obtener_datos():
    try:
        # 500 Velas y 500 Puntas
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
        
        # Profundidad 500
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        v_comp = sum(float(bid[1]) for bid in depth['bids']) 
        v_vent = sum(float(ask[1]) for ask in depth['asks'])  
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema, v_comp, v_vent
    except Exception as e:
        print(f"🔄 Error momentáneo de datos: {e}")
        return None, None, None, None, None, None, None, None

def main_loop():
    print(f"🔱 GLADIADOR v12.9.4 - BLINDAJE TOTAL")
    while True:
        data = obtener_datos()
        if data[0] is not None:
            p, p_di, m_di, adx, cap, ema, v_comp, v_vent = data
            try:
                pos = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                
                if amt == 0:
                    ventaja = abs(p_di - m_di)
                    print(f"🔎 P:{p:.1f} | DI:{ventaja:.1f} | L-Com:{v_comp:.0f} L-Ven:{v_vent:.0f}")
                    
                    if p > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                    elif p < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                else:
                    # Salida táctica
                    if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                        client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
            except Exception as e:
                print(f"⚠️ Alerta en loop: {e}")
        
        sys.stdout.flush()
        time.sleep(15)

if __name__ == "__main__":
    main_loop()
