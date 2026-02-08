import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread, Lock
from flask import Flask

# --- 🧠 PIZARRA DE DATOS (Memoria compartida entre Cerebro y Ejecutor) ---
pizarra = {
    "señal": "ESPERAR",
    "precio": 0,
    "ema": 0,
    "vol_c": 0,
    "vol_v": 0,
    "status": "Iniciando..."
}
candado = Lock()

# ==========================================
# 🛡️ 1. EL EJECUTOR (Mantiene vivo el bot y opera)
# ==========================================
app = Flask('')

@app.route('/')
def health():
    with candado:
        # Railway verá que el bot siempre está respondiendo
        return f"🔱 Gladiador Activo - Estado: {pizarra['status']} | Señal: {pizarra['señal']}", 200

def servidor_web():
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto)

# Lanzamos el servidor de vida de inmediato
Thread(target=servidor_web, daemon=True).start()

# ==========================================
# 🛡️ 2. EL CEREBRO (Analista Industrial de 500 Puntas)
# ==========================================
def cerebro_analista():
    SIMBOLO = 'ETHUSDT'
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    print("🧠 Cerebro: Analizando mercado...")
    
    while True:
        try:
            # 📊 Velas y DMI (300 velas para precisión total)
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=300)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # Cálculos de DMI para filtrar entradas
            plus_dm = df['high'].diff().clip(lower=0)
            minus_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
            atr = tr.rolling(window=14).mean()
            p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
            m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
            adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0

            # 📚 Libro de 500 Puntas (Tu estrategia estrella)
            depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
            vol_c = sum(float(b[1]) for b in depth['bids'])
            vol_v = sum(float(a[1]) for a in depth['asks'])

            # Escribir en la pizarra para el soldado
            with candado:
                pizarra['precio'] = p_act
                pizarra['ema'] = ema_200
                pizarra['vol_c'] = vol_c
                pizarra['vol_v'] = vol_v
                
                # Definición de señal
                if p_act > (ema_200 + 1) and p_di > (m_di + 12) and adx > 25 and vol_c > vol_v:
                    pizarra['señal'] = "LONG"
                elif p_act < (ema_200 - 1) and m_di > (p_di + 12) and adx > 25 and vol_v > vol_c:
                    pizarra['señal'] = "SHORT"
                else:
                    pizarra['señal'] = "ESPERAR"
                
                pizarra['status'] = "Análisis 500/300 Completado"

        except Exception as e:
            print(f"🧠 Cerebro: Esperando datos... {e}")
            time.sleep(10)
        
        time.sleep(15)

# ==========================================
# 🛡️ 3. EL SOLDADO (Compra y Venta)
# ==========================================
def soldado_ejecutor():
    SIMBOLO = 'ETHUSDT'
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    print("⚔️ Soldado: Listo para ejecutar órdenes.")
    
    while True:
        try:
            with candado:
                señal = pizarra['señal']
                p_actual = pizarra['precio']

            # Revisar posición actual
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)

            if amt == 0 and señal != "ESPERAR":
                # Interés Compuesto (20% de capital)
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p_actual, 3)
                
                side = 'BUY' if señal == "LONG" else 'SELL'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=qty)
                print(f"⚔️ SOLDADO: ¡Ataque {side} enviado!")
            
            elif amt != 0:
                # Cierre si la señal cambia o el precio cruza la EMA
                if (amt > 0 and señal == "SHORT") or (amt < 0 and señal == "LONG"):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("⚔️ SOLDADO: Posición cerrada por orden del Cerebro.")

        except Exception as e:
            # El soldado no se rinde, sigue esperando la pizarra
            pass
            
        sys.stdout.flush()
        time.sleep(5) # El soldado vigila la pizarra cada 5 segundos

if __name__ == "__main__":
    # Arrancamos el Cerebro en segundo plano
    Thread(target=cerebro_analista, daemon=True).start()
    # El Soldado corre en el proceso principal
    soldado_ejecutor()
