import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. EL PUENTE (SERVIDOR DE VIDA PRIORITARIO)
# ==========================================
app = Flask('')

@app.route('/')
def health_check():
    # Este proceso nunca se detiene, es el que mantiene vivo el bot en Railway
    return "🛡️ Puente Gladiador v12.12.0 Online", 200

def run_flask():
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto, debug=False, use_reloader=False)

# Lanzamos el puente inmediatamente en un hilo independiente
Thread(target=run_flask, daemon=True).start()

# ==========================================
# 🛡️ 2. EL OBRERO (ANÁLISIS DE REBANADAS)
# ==========================================
SIMBOLO = 'ETHUSDT'
LEVERAGE = 10
PORCENTAJE_OP = 0.20

def motor_trading():
    print("🚀 Motor de Trading Gladiador Iniciado...")
    time.sleep(5) # Pausa para que el puente se estabilice
    
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    except Exception as e:
        print(f"❌ Error API: {e}")
        return

    while True:
        try:
            # 📊 PASO A: El Libro en rebanada ligera (100)
            # Pedimos 100 para que la respuesta sea instantánea
            depth = client.futures_order_book(symbol=SIMBOLO, limit=100)
            v_comp = sum(float(bid[1]) for bid in depth['bids'])
            v_vent = sum(float(ask[1]) for ask in depth['asks'])

            # 📊 PASO B: Velas (200 para EMA perfecta)
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=200)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            p_act = df['close'].iloc[-1]
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]

            # 🔍 REVISIÓN DE POSICIÓN
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)

            print(f"🔎 P:{p_act:.1f} | EMA:{ema:.1f} | L-Comp:{v_comp:.0f}")

            # Lógica de Gatillo (Simplificada para estabilidad inicial)
            if amt == 0:
                if p_act > (ema + 1) and v_comp > v_vent:
                    print("🔥 EJECUTANDO LONG")
                    # (Aquí va tu orden de compra)
            
        except Exception as e:
            # Si el obrero falla, el puente de arriba sigue vivo
            print(f"📡 Sincronizando: {e}")
            time.sleep(10)
            
        sys.stdout.flush()
        time.sleep(15)

# ==========================================
# 🛡️ 3. ARRANQUE DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    # El motor corre en el proceso principal, pero el puente ya está arriba
    motor_trading()
