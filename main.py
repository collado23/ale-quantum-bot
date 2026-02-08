import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. EL MURO DE CARGA (PUENTE WEB)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    # Este es el "latido" que mantiene a Railway tranquilo
    return "🔱 Gladiador v12.14.0: Sistema Blindado Activo", 200

def ejecutar_puente():
    puerto = int(os.environ.get("PORT", 8080))
    # Desactivamos logs de Flask para ahorrar procesador
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=puerto)

# Lanzamos el puente web inmediatamente
Thread(target=ejecutar_puente, daemon=True).start()

# ==========================================
# 🛡️ 2. CONFIGURACIÓN ESTRATÉGICA INDUSTRIAL
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # 20% del capital para interés compuesto
LEVERAGE = 10          
FILTRO_DI = 12.0       # Diferencia mínima DI+ y DI-
ADX_MINIMO = 25.0      # Fuerza de tendencia
DISTANCIA_EMA = 1.0    # Margen sobre la EMA 200

def motor_principal():
    print("🚀 INICIANDO BLINDAJE TOTAL - GLADIADOR v12.14.0")
    time.sleep(5)
    
    try:
        # Configuración de Cliente
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("✅ Conexión con Binance establecida.")
    except Exception as e:
        print(f"❌ Error API: {e}")
        return

    while True:
        try:
            # 📊 PASO 1: ANÁLISIS DE VELAS (250 velas para EMA exacta)
            klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=250)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            p_act = df['close'].iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            # Cálculos de Fuerza (DMI y ADX)
            plus_dm = df['high'].diff().clip(lower=0)
            minus_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high'] - df['low'], 
                            np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                       abs(df['low'] - df['close'].shift(1))))
            atr = tr.rolling(window=14).mean()
            p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
            m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
            adx_val = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
            
            # 📚 PASO 2: EL LIBRO DE LAS 500 PUNTAS
            depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
            v_comp = sum(float(bid[1]) for bid in depth['bids'])
            v_vent = sum(float(ask[1]) for ask in depth['asks'])
            
            # 💰 PASO 3: GESTIÓN DE CAPITAL
            balance = client.futures_account_balance()
            cap_usdt = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
            
            # REVISIÓN DE POSICIÓN
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)

            # LOGS DE ESTADO (Para que veas la magia en Railway)
            print(f"🔹 P:{p_act:.1f} | EMA:{ema_200:.1f} | ADX:{adx_val:.1f} | L-Comp:{v_comp:.0f} | L-Vent:{v_vent:.0f}")

            if amt == 0:
                # 🏹 GATILLO COMPRA (LONG)
                if p_act > (ema_200 + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx_val > ADX_MINIMO and v_comp > v_vent:
                    qty = round(((cap_usdt * PORCENTAJE_OP) * LEVERAGE) / p_act, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                    print(f"🔥 ATAQUE LONG EJECUTADO: {qty} ETH")

                # 🏹 GATILLO VENTA (SHORT)
                elif p_act < (ema_200 - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx_val > ADX_MINIMO and v_vent > v_comp:
                    qty = round(((cap_usdt * PORCENTAJE_OP) * LEVERAGE) / p_act, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                    print(f"📉 ATAQUE SHORT EJECUTADO: {qty} ETH")
            
            else:
                # 🛑 GESTIÓN DE SALIDA (Asegura ganancias o corta pérdidas)
                if (amt > 0 and (p_act < ema_200 or m_di > p_di)) or (amt < 0 and (p_act > ema_200 or p_di > m_di)):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("🛑 CIERRE DE POSICIÓN POR SEÑAL OPUESTA")

        except Exception as e:
            print(f"📡 Sincronizando sistema... {e}")
            time.sleep(10)
            
        sys.stdout.flush()
        time.sleep(15) # Pausa de seguridad para el CPU de Railway

if __name__ == "__main__":
    motor_principal()
