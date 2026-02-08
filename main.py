import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread, Lock
from flask import Flask

# --- PIZARRA DE MEMORIA (Compartida entre Cerebro y Ejecutor) ---
pizarra = {
    "accion": "ESPERAR",
    "precio": 0,
    "vol_comp": 0,
    "vol_vent": 0,
    "ema": 0,
    "qty": 0,
    "status": "Iniciando..."
}
lock = Lock()

# ==========================================
# 🛡️ 1. EL EJECUTOR (Mantiene vivo el bot y opera)
# ==========================================
app = Flask('')

@app.route('/')
def live():
    with lock:
        return f"🔱 Gladiador Activo - Estado: {pizarra['status']} | Acción: {pizarra['accion']}", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Lanzamos al ejecutor web de inmediato
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🛡️ 2. EL CEREBRO (Análisis Industrial)
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20
LEVERAGE = 10

def cerebro_analista():
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    print("🧠 Cerebro Analista: Despierto y conectando...")
    
    while True:
        try:
            # 📊 Análisis de 300 Velas y DMI
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=300)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # DMI / ADX
            plus_dm = df['high'].diff().clip(lower=0)
            minus_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
            atr = tr.rolling(window=14).mean()
            p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
            m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
            adx_val = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
            
            # 📚 Análisis de 500 Puntas del Libro
            depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
            v_comp = sum(float(bid[1]) for bid in depth['bids'])
            v_vent = sum(float(ask[1]) for ask in depth['asks'])

            # Escribir conclusiones en la pizarra
            with lock:
                pizarra['precio'] = p_act
                pizarra['ema'] = ema_200
                pizarra['vol_comp'] = v_comp
                pizarra['vol_vent'] = v_vent
                
                if p_act > (ema_200 + 1) and p_di > (m_di + 12) and adx_val > 25 and v_comp > v_vent:
                    pizarra['accion'] = "COMPRAR"
                elif p_act < (ema_200 - 1) and m_di > (p_di + 12) and adx_val > 25 and v_vent > v_comp:
                    pizarra['accion'] = "VENDER"
                else:
                    pizarra['accion'] = "ESPERAR"
                
                pizarra['status'] = "Analizado 500/300 OK"

        except Exception as e:
            print(f"🧠 Cerebro: Error de saturación, reiniciando ciclo... {e}")
            time.sleep(10)
        
        time.sleep(15)

# ==========================================
# 🛡️ 3. EL SOLDADO (Ejecución de órdenes)
# ==========================================
def soldado_ejecutor():
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    while True:
        try:
            with lock:
                accion = pizarra['accion']
                p = pizarra['precio']
                v_c = pizarra['vol_comp']
            
            # Revisar si ya hay posición
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)

            if amt == 0 and accion != "ESPERAR":
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                
                side = 'BUY' if accion == "COMPRAR" else 'SELL'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=qty)
                print(f"⚔️ SOLDADO: Orden {side} ejecutada por orden del Cerebro.")
            
            elif amt != 0:
                # Lógica de cierre si el cerebro cambia de opinión
                if (amt > 0 and accion == "VENDER") or (amt < 0 and accion == "COMPRAR"):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("⚔️ SOLDADO: Posición cerrada.")

        except Exception as e:
            print(f"⚔️ Soldado: Esperando señal... {e}")
        
        time.sleep(5) # El soldado vigila la pizarra cada 5 segundos

# Lanzamos los hilos
if __name__ == "__main__":
    Thread(target=cerebro_analista, daemon=True).start()
    soldado_ejecutor()
