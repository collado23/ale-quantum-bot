import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- SEGURIDAD ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gladiador v12.5: Escudo de Capital Activo"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS TÁCTICOS v12.5 (AGRESIVO)
# ==========================================
NOMBRE_BOT = "GLADIADOR v12.5"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # Seguimos al 20% para cuidar el resto
LEVERAGE = 10          
ADX_ENTRADA = 25.0     # Subimos a 25 para entrar solo en tendencia real
ADX_SALIDA_BASE = 20.0 # Salimos antes si la fuerza muere
DISTANCIA_EMA = 2.0    # Más pegado a la EMA para no entrar tarde

client = Client(API_KEY, SECRET_KEY)

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_actual = df['close'].iloc[-1]
        
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        p_di_s = 100 * (plus_dm.rolling(window=14).mean() / atr)
        m_di_s = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(p_di_s - m_di_s) / (p_di_s + m_di_s)
        adx_s = dx.rolling(window=14).mean()
        
        return p_actual, p_di_s.iloc[-1], m_di_s.iloc[-1], adx_s.iloc[-1], ema200
    except Exception as e:
        print(f"📡 Error de red: {e}")
        return None, None, None, None, None

def gestionar_posicion_actual():
    try:
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        pos_info = client.futures_position_information(symbol=SIMBOLO)
        pos = next(p for p in pos_info if p['symbol'] == SIMBOLO)
        amt = float(pos['positionAmt'])
        
        if amt > 0: return True, 'LONG', abs(amt), cap
        elif amt < 0: return True, 'SHORT', abs(amt), cap
        else: return False, None, 0, cap
    except:
        return False, None, 0, 0

def cerrar_todo(motivo):
    try:
        pos_info = client.futures_position_information(symbol=SIMBOLO)
        pos = next(p for p in pos_info if p['symbol'] == SIMBOLO)
        amt = float(pos['positionAmt'])
        if amt != 0:
            side = 'SELL' if amt > 0 else 'BUY'
            client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=abs(amt))
            print(f"🛑 CIERRE DE EMERGENCIA: {motivo}")
            return True
    except Exception as e:
        print(f"❌ Error al cerrar: {e}")
    return False

def main_loop():
    print(f"🚀 {NOMBRE_BOT} - PROTEGIENDO CAPITAL")
    
    while True:
        p, p_di, m_di, adx, ema = obtener_datos()
        en_pos, tipo, cant, cap = gestionar_posicion_actual()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            emoji = "🐂" if p_di > m_di else "🐻"
            
            if not en_pos:
                print(f"🔎 [{hora}] {emoji} | ADX: {adx:.1f} | P: {p:.1f} | EMA: {ema:.1f}")
                
                # ENTRADA LONG (Solo si el Toro es MUCHO más fuerte)
                if p > (ema + DISTANCIA_EMA) and adx >= ADX_ENTRADA and p_di > (m_di + 7):
                    qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                    print(f"🔥 COMPRA (LONG) GATILLADA")
                
                # ENTRADA SHORT (Para ganar en la caída)
                elif p < (ema - DISTANCIA_EMA) and adx >= ADX_ENTRADA and m_di > (p_di + 7):
                    qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                    print(f"📉 VENTA (SHORT) GATILLADA")

            else:
                # GESTIÓN DE SALIDA AGRESIVA
                if tipo == 'LONG':
                    # Si el precio cae de la EMA o el oso se vuelve muy fuerte, fuera.
                    if p < ema or adx < ADX_SALIDA_BASE or m_di > p_di:
                        cerrar_todo("Protección contra caída")
                
                elif tipo == 'SHORT':
                    # Si el precio sube de la EMA o el toro se vuelve muy fuerte, fuera.
                    if p > ema or adx < ADX_SALIDA_BASE or p_di > m_di:
                        cerrar_todo("Protección contra rebote")
            
            sys.stdout.flush()
        time.sleep(15) # Revisión más rápida (cada 15 seg)

if __name__ == "__main__":
    if app: Thread(target=run_web, daemon=True).start()
    main_loop()
