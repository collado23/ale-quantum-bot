import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. SERVIDOR DE VIDA (RAILWAY COMPATIBLE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Gladiador v12.9.6 Quantum: 500 Velas + 500 Puntas Online", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Lanzamiento inmediato del servidor para evitar el 'Stopping Container'
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🛡️ 2. CONFIGURACIÓN TÁCTICA
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # Maneja el 20% para Interés Compuesto
LEVERAGE = 10          
FILTRO_DI = 12.0       # Ventaja mínima del Toro/Oso
ADX_MINIMO = 25.0      
DISTANCIA_EMA = 2.0    

# Conexión inicial segura
try:
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
except Exception as e:
    print(f"❌ Error crítico en llaves API: {e}")

def obtener_analisis_quantum():
    """Analiza la profundidad real del mercado (500/500)"""
    try:
        # 📊 DESCARGA DE 500 VELAS
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        # Indicadores sobre base de 500
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
        
        # 📚 LIBRO DE ÓRDENES (500 PUNTAS)
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        vol_compras = sum(float(bid[1]) for bid in depth['bids']) 
        vol_ventas = sum(float(ask[1]) for ask in depth['asks'])  
        
        # Capital actual para Interés Compuesto
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_act, p_di, m_di, adx_val, cap, ema, vol_compras, vol_ventas
    except Exception as e:
        print(f"📡 Sincronizando con Binance... ({e})")
        return None

def main_loop():
    print(f"🔱 GLADIADOR v12.9.6 - MODO INDUSTRIAL")
    print(f"⚙️ Config: 500 Velas | 500 Puntas Libro | Filtro DI: {FILTRO_DI}")
    
    while True:
        res = obtener_analisis_quantum()
        
        if res:
            p, p_di, m_di, adx, cap, ema, v_comp, v_vent = res
            try:
                # Verificación de posición
                pos = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                
                if amt == 0:
                    ventaja = abs(p_di - m_di)
                    print(f"🔎 P:{p:.1f} | DI:{ventaja:.1f} | L-Com:{v_comp:.0f} L-Ven:{v_vent:.0f}")
                    
                    # --- GATILLO LONG ---
                    if p > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                        print(f"🔥 COMPRA QUANTUM: Libro y Tendencia a favor.")
                    
                    # --- GATILLO SHORT ---
                    elif p < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                        print(f"📉 VENTA QUANTUM: Libro y Tendencia a favor.")
                
                else:
                    # SALIDA TÉCNICA (Hachazo + Debilidad Libro/DI)
                    if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                        client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                        print(f"🛑 CIERRE: Protegiendo capital.")

            except Exception as e:
                print(f"⚠️ Alerta: {e}")
        
        sys.stdout.flush()
        time.sleep(15)

if __name__ == "__main__":
    main_loop()
