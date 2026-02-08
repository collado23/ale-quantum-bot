import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. EL PUENTE DE HIERRO (Mantiene vivo el bot)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🔱 Gladiador v12.13.0: Puente de Hierro Activo", 200

def run_flask():
    # Railway necesita una respuesta constante en este puerto
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=puerto, debug=False, use_reloader=False)

# Iniciamos el puente en un hilo secundario para que no interfiera
Thread(target=run_flask, daemon=True).start()

# ==========================================
# 🛡️ 2. CONFIGURACIÓN TÁCTICA ALE
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # Interés compuesto al 20%
LEVERAGE = 10          # Apalancamiento x10
FILTRO_DI = 12.0       # Fuerza mínima del movimiento
ADX_MINIMO = 25.0      # Confirmación de tendencia
DISTANCIA_EMA = 1.5    # Margen sobre la EMA 200

def motor_trading_quantum():
    print("🚀 GLADIADOR v12.13.0 - INICIANDO SISTEMA INDUSTRIAL...")
    time.sleep(10) # Tiempo de gracia para estabilización
    
    try:
        api = os.getenv('API_KEY')
        sec = os.getenv('API_SECRET')
        client = Client(api, sec)
        print("✅ Conexión con Binance asegurada.")
    except Exception as e:
        print(f"❌ Error API: {e}")
        return

    while True:
        try:
            # 📊 PASO 1: ANÁLISIS DE VELAS (250 velas para EMA 200 exacta)
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=250)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # Cálculos de Fuerza DMI / ADX
            plus_dm = df['high'].diff().clip(lower=0)
            minus_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
            atr = tr.rolling(window=14).mean()
            p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
            m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
            adx_val = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
            
            # 📚 PASO 2: EL LIBRO DE LAS 500 PUNTAS (REBANADAS)
            depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
            v_comp = sum(float(bid[1]) for bid in depth['bids'][:500])
            v_vent = sum(float(ask[1]) for ask in depth['asks'][:500])
            
            # 💰 PASO 3: GESTIÓN DE CAPITAL (INTERÉS COMPUESTO)
            balance = client.futures_account_balance()
            cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
            
            # 🔍 REVISAR POSICIÓN ACTUAL
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)

            # ESTADO EN PANTALLA
            print(f"🔎 P:{p_act:.1f} | EMA:{ema:.1f} | DI+:{p_di:.1f} | DI-:{m_di:.1f} | L-C:{v_comp:.0f}")

            if amt == 0:
                # 🏹 GATILLO LONG
                if p_act > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx_val > ADX_MINIMO and v_comp > v_vent:
                    qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p_act, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                    print(f"🔥 ATAQUE LONG: {qty} ETH")

                # 🏹 GATILLO SHORT
                elif p_act < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx_val > ADX_MINIMO and v_vent > v_comp:
                    qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p_act, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                    print(f"📉 ATAQUE SHORT: {qty} ETH")
            
            else:
                # 🛑 CIERRE TÉCNICO (Salida por cruce de EMA o debilidad DI)
                if (amt > 0 and (p_act < ema or m_di > p_di)) or (amt < 0 and (p_act > ema or p_di > m_di)):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("🛑 CIERRE DE SEGURIDAD")

        except Exception as e:
            print(f"📡 Sincronizando puente... {e}")
            time.sleep(5)
            
        sys.stdout.flush()
        time.sleep(15) # Ciclo de 15 segundos para estabilidad total

# ==========================================
# 🛡️ 3. ARRANQUE
# ==========================================
if __name__ == "__main__":
    motor_trading_quantum()
