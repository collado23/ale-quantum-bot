import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread, Lock
from flask import Flask

# --- 🧠 PIZARRA DE COMANDO (Comunicación interna) ---
pizarra = {
    "señal": "ESPERAR",
    "p_act": 0,
    "v_comp": 0,
    "v_vent": 0,
    "status": "Iniciando..."
}
candado = Lock()

# ==========================================
# 🛡️ 1. EL SOLDADO (EJECUTOR Y SERVIDOR DE VIDA)
# ==========================================
app = Flask('')

@app.route('/')
def health():
    with candado:
        # Esto le dice a Railway que el bot está sano
        return f"🔱 Gladiador Online | {pizarra['status']} | Señal: {pizarra['señal']}", 200

def run_flask():
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto)

# Lanzamos al servidor de vida inmediatamente
Thread(target=run_flask, daemon=True).start()

# ==========================================
# 🛡️ 2. EL CEREBRO (ANÁLISIS INDUSTRIAL)
# ==========================================
def cerebro_analista():
    SIMBOLO = 'ETHUSDT'
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    print("🧠 Cerebro: Analizando mercado...")
    
    while True:
        try:
            # 📊 Análisis de 250 Velas (Punto dulce para EMA 200)
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=250)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # Fuerza DMI / ADX
            plus_dm = df['high'].diff().clip(lower=0)
            minus_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
            atr = tr.rolling(window=14).mean()
            p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
            m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

            # 📚 Libro de 500 Puntas (Barrido Quantum)
            depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
            v_c = sum(float(b[1]) for b in depth['bids'])
            v_v = sum(float(a[1]) for a in depth['asks'])

            # Escribir en la pizarra para el Soldado
            with candado:
                pizarra['p_act'] = p_act
                pizarra['v_comp'] = v_c
                pizarra['v_vent'] = v_v
                
                if p_act > (ema_200 + 1) and p_di > (m_di + 12) and adx > 25 and v_c > v_v:
                    pizarra['señal'] = "LONG"
                elif p_act < (ema_200 - 1) and m_di > (p_di + 12) and adx > 25 and v_v > v_c:
                    pizarra['señal'] = "SHORT"
                else:
                    pizarra['señal'] = "ESPERAR"
                pizarra['status'] = "Cerebro OK"

        except Exception as e:
            print(f"🧠 Cerebro: Sincronizando... {e}")
            time.sleep(10)
        
        time.sleep(15) # Ciclo de descanso para el CPU

# ==========================================
# 🛡️ 3. EL SOLDADO (ORDENES DE COMPRA/VENTA)
# ==========================================
def soldado_ejecutor():
    SIMBOLO = 'ETHUSDT'
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    print("⚔️ Soldado: Listo para la acción.")
    
    while True:
        try:
            with candado:
                señal = pizarra['señal']
                p_actual = pizarra['p_act']
                v_c = pizarra['v_comp']
                v_v = pizarra['v_vent']

            # Revisar posición actual
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)

            print(f"🔎 P:{p_actual:.1f} | L-Comp:{v_c:.0f} | L-Ven:{v_v:.0f}")

            if amt == 0 and señal != "ESPERAR":
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p_actual, 3) # Interés compuesto 20%
                
                side = 'BUY' if señal == "LONG" else 'SELL'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=qty)
                print(f"🔥 SOLDADO: Ejecutando {side}")
            
            elif amt != 0:
                # Cierre por señal opuesta
                if (amt > 0 and señal == "SHORT") or (amt < 0 and señal == "LONG"):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("🛑 SOLDADO: Cerrando posición")

        except Exception as e:
            pass
            
        sys.stdout.flush()
        time.sleep(5)

if __name__ == "__main__":
    # Arrancamos el Cerebro en un hilo
    Thread(target=cerebro_analista, daemon=True).start()
    # El Soldado corre en el proceso principal
    soldado_ejecutor()
