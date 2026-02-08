import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. EL PUENTE (SERVIDOR DE VIDA)
# ==========================================
app = Flask('')

@app.route('/')
def health_check():
    # Este es el puente que Railway ve siempre activo
    return "🛡️ Puente Quantum v12.12.0: ACTIVO", 200

def iniciar_servidor():
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto)

# Arrancamos el puente de inmediato en un hilo separado
Thread(target=iniciar_servidor, daemon=True).start()

# ==========================================
# 🛡️ 2. EL OBRERO (ANÁLISIS DE REBANADAS)
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20
LEVERAGE = 10

def motor_quantum():
    print("🚀 Motor Gladiador Iniciado...")
    # Esperamos que el puente se estabilice
    time.sleep(5)
    
    try:
        api = os.getenv('API_KEY')
        sec = os.getenv('API_SECRET')
        client = Client(api, sec)
    except:
        print("❌ Error de llaves API")
        return

    while True:
        try:
            # 📚 BARRIDO DE LIBRO (Rebanada de 100)
            # Pedimos 100 para que sea instantáneo y no cuelgue el puente
            depth = client.futures_order_book(symbol=SIMBOLO, limit=100)
            v_comp = sum(float(bid[1]) for bid in depth['bids'])
            v_vent = sum(float(ask[1]) for ask in depth['asks'])

            # 📊 VELAS (200 para EMA exacta)
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=200)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            p_act = df['close'].iloc[-1]
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]

            # 🔱 LÓGICA DE GATILLO
            print(f"🔎 P:{p_act:.1f} | EMA:{ema:.1f} | Libro-Comp:{v_comp:.0f}")
            
            # (Aquí irían tus órdenes de compra/venta como antes)
            
        except Exception as e:
            # Si hay error en Binance, el puente (Flask) sigue vivo
            print(f"📡 Sincronizando puente... {e}")
            time.sleep(10)
            
        sys.stdout.flush()
        time.sleep(15)

# ==========================================
# 🛡️ 3. EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    # El motor corre independiente del servidor para que no se maten entre ellos
    motor_quantum()
