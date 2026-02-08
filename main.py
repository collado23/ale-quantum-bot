import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. SERVIDOR DE VIDA (RAILWAY OK)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🛡️ Gladiador v12.11.0: Modo Rebanadas 5x100 Activo", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Lanzamiento flash para evitar el 'Stopping Container'
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🛡️ 2. CONFIGURACIÓN INDUSTRIAL
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   
LEVERAGE = 10          
FILTRO_DI = 12.0       
ADX_MINIMO = 25.0      

def obtener_datos_rebanados():
    """Estrategia Ale: Carga progresiva para no colgar el bot"""
    try:
        api = os.getenv('API_KEY')
        sec = os.getenv('API_SECRET')
        client = Client(api, sec)
        
        # 📊 PASO 1: Velas (250 es el punto dulce)
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=250)
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
        
        # 🛡️ PASO 2: El Libro de 500 en rebanadas de 100
        # Pedimos el libro total de 500 pero lo procesamos con pausas para el CPU
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        
        v_comp = sum(float(bid[1]) for bid in depth['bids'][:500])
        time.sleep(0.2) # Micro-descanso para el procesador
        v_vent = sum(float(ask[1]) for ask in depth['asks'][:500])
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema, v_comp, v_vent, client
    except Exception as e:
        print(f"📡 Sincronizando: {e}")
        return None

def main_loop():
    print(f"🔱 GLADIADOR v12.11.0 - BARRIDO PROGRESIVO 500")
    
    while True:
        data = obtener_datos_rebanados()
        
        if data:
            p, p_di, m_di, adx, cap, ema, v_comp, v_vent, client = data
            try:
                pos = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                
                if amt == 0:
                    print(f"🔎 P:{p:.1f} | EMA:{ema:.1f} | L-Com:{v_comp:.0f} L-Ven:{v_vent:.0f}")
                    
                    # Lógica de Gatillo Quantum
                    if p > (ema + 1) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                        print("🚀 LONG ENVIADO")
                    elif p < (ema - 1) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                        print("📉 SHORT ENVIADO")
                else:
                    # Salida táctica
                    if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                        client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                        print("🛑 CIERRE")

            except Exception as e:
                print(f"⚠️ Reintentando ciclo: {e}")
        
        sys.stdout.flush()
        time.sleep(20) # 20 segundos para que Railway respire entre barridos

if __name__ == "__main__":
    main_loop()
