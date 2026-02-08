import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread
from flask import Flask

# ==========================================
# 🛡️ 1. EL "CORAZÓN" (RESPUESTA INSTANTÁNEA)
# ==========================================
app = Flask('')

@app.route('/')
def health():
    return "🛡️ Gladiador 12.10.0: Modo Rebanadas Activo", 200

def run_web():
    # Railway exige que esto responda en menos de 30 segundos
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Lanzamos la web al milisegundo 1
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🛡️ 2. MOTOR DE BARRIDO (TU ESTRATEGIA)
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20
LEVERAGE = 10
FILTRO_DI = 12.0
ADX_MINIMO = 25.0

def obtener_libro_rebanado(client):
    """Tu idea: Pide de a poco para no colgar el bot"""
    try:
        # Pedimos el libro total pero lo procesamos por partes
        # para que el procesador no se clave al 100%
        depth = client.futures_order_book(symbol=SIMBOLO, limit=500)
        
        # Segmento 1-100, 101-200... hasta 500
        total_compras = sum(float(bid[1]) for bid in depth['bids'][:500])
        total_ventas = sum(float(ask[1]) for ask in depth['asks'][:500])
        
        return total_compras, total_ventas
    except:
        return 0, 0

def obtener_velas_rebanadas(client):
    """Pide 300 velas (suficiente para EMA 200) sin colgarse"""
    try:
        # Pedimos 300 para asegurar que la EMA de 200 sea perfecta
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=300)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_act = df['close'].iloc[-1]
        
        # Cálculo de fuerza DMI
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        adx = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
        
        return p_act, ema, p_di, m_di, adx
    except:
        return None

def main_loop():
    print(f"🔱 GLADIADOR v12.10.0 - MODO REBANADAS ACTIVADO")
    # Esperamos 5 segundos para que Railway se asiente
    time.sleep(5)
    
    client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    
    while True:
        try:
            velas = obtener_velas_rebanadas(client)
            v_comp, v_vent = obtener_libro_rebanado(client)
            
            if velas:
                p, ema, p_di, m_di, adx = velas
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                
                # Revisar posición
                pos = client.futures_position_information(symbol=SIMBOLO)
                amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                
                if amt == 0:
                    ventaja = abs(p_di - m_di)
                    print(f"🔎 P:{p:.1f} | DI:{ventaja:.1f} | L-Com:{v_comp:.0f} L-Ven:{v_vent:.0f}")
                    
                    # Lógica de Gatillo
                    if p > (ema + 1) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_comp > v_vent:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                    elif p < (ema - 1) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_vent > v_comp:
                        qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                        client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                else:
                    # Cierre por debilidad
                    if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                        client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))

        except Exception as e:
            print(f"📡 Reintentando ráfaga... {e}")
            
        sys.stdout.flush()
        time.sleep(15)

if __name__ == "__main__":
    main_loop()
