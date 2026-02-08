import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from threading import Thread
from flask import Flask

# ==========================================
# 🔱 ESCUDO ANTI-CAÍDAS RAILWAY (INMORTAL)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🛡️ Gladiador v12.9.2 Quantum: 500 Velas + 500 Puntas Activo"

def run_web():
    # Railway necesita una respuesta inmediata por el puerto asignado
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Iniciamos el servidor web en un hilo aparte antes de cargar datos pesados
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🔱 CONFIGURACIÓN DE CONEXIÓN Y ESTRATEGIA
# ==========================================
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')
client = Client(API_KEY, SECRET_KEY)

SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # 20% de tus $34.5
LEVERAGE = 10          
FILTRO_DI = 12.0       # <--- LA BARRERA DE HIERRO
ADX_MINIMO = 25.0      
DISTANCIA_EMA = 2.0    

def obtener_datos_industriales():
    """Analiza 500 velas y 500 órdenes de profundidad"""
    try:
        # 🛡️ 1. ANÁLISIS DE MEMORIA (500 VELAS)
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        # EMA 200 de precisión
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # DMI / ADX con toda la data de 500 velas
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx_val = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        # 🛡️ 2. ANÁLISIS QUANTUM (500 PUNTAS DEL LIBRO)
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        vol_compras = sum(float(bid[1]) for bid in depth['bids']) 
        vol_ventas = sum(float(ask[1]) for ask in depth['asks'])  
        
        # 🛡️ 3. SALDO PARA INTERÉS COMPUESTO
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema, vol_compras, vol_ventas
        
    except Exception as e:
        print(f"📡 Buscando conexión... {e}")
        return None, None, None, None, None, None, None, None

def main_loop():
    print(f"🔱 GLADIADOR v12.9.2 - SISTEMA INDUSTRIAL ACTIVADO")
    print(f"💰 Operando con 20% de capital y x10 de apalancamiento.")
    
    while True:
        p, p_di, m_di, adx, cap, ema, v_comp, v_vent = obtener_datos_industriales()
        
        if p is not None:
            try:
                # Revisar posición actual en Binance
                pos = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                
                # --- LÓGICA DE GATILLO (BUSCANDO ENTRADA) ---
                if amt == 0:
                    diff_di = abs(p_di - m_di)
                    print(f"🔎 P:{p:.1f} | EMA:{ema:.1f} | VentajaDI:{diff_di:.1f} | L-Com:{v_comp:.0f} L-Ven:{v_vent:.0f}")
                    
                    # LONG: EMA + DMI (12 pts) + ADX + LIBRO A FAVOR
                    if p > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                        print(f"🚀 GATILLO LONG: Confirmación por Libro y Tendencia.")
                    
                    # SHORT: EMA + DMI (12 pts) + ADX + LIBRO A FAVOR
                    elif p < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                        print(f"📉 GATILLO SHORT: Confirmación por Libro y Tendencia.")
                
                # --- LÓGICA DE SALIDA (POSICIÓN ABIERTA) ---
                else:
                    # El Hachazo: Cambio de EMA o pérdida de fuerza DI
                    if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                        side_c = 'SELL' if amt > 0 else 'BUY'
                        client.futures_create_order(symbol=SIMBOLO, side=side_c, type='MARKET', quantity=abs(amt))
                        print(f"🛑 CIERRE TÁCTICO: Protegiendo capital actual.")

            except Exception as e:
                print(f"⚠️ Alerta en ejecución: {e}")
            
            sys.stdout.flush()
        time.sleep(15)

if __name__ == "__main__":
    main_loop()
