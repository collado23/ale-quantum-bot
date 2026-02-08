import time
import sys
import os
import pandas as pd
import numpy as np
from binance.client import Client
from threading import Thread

# --- CONFIGURACIÓN DE SEGURIDAD ---
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('API_SECRET')

# --- ESCUDO ANTI-PAUSA (FLASK) ---
try:
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "Gladiador v12.4: Operando Long & Short"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS TÁCTICOS v12.4 (COMPLETO)
# ==========================================
NOMBRE_BOT = "GLADIADOR v12.4"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # 20% de capital por operación
LEVERAGE = 10          
ADX_ENTRADA = 22.0     
ADX_SALIDA_BASE = 15.0 
ADX_SALIDA_SNIPER = 25.0 
DISTANCIA_EMA = 5.0    

client = Client(API_KEY, SECRET_KEY)
en_posicion = False
tipo_posicion = None 

def obtener_datos():
    try:
        klines = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=500)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        
        # EMA 200 para tendencia macro
        ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        p_actual = df['close'].iloc[-1]
        
        # CÁLCULO DE ADX Y DI+/-
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        dx = 100 * abs(p_di - m_di) / (p_di + m_di)
        adx_val = dx.rolling(window=14).mean().iloc[-1]
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_actual, p_di, m_di, adx_val, cap, ema200
    except Exception as e:
        print(f"📡 Sincronizando datos... {e}")
        return None, None, None, None, None, None

def cerrar_posicion(motivo):
    global en_posicion, tipo_posicion
    try:
        info = client.futures_position_information(symbol=SIMBOLO)
        pos = next(p for p in info if p['symbol'] == SIMBOLO)
        cantidad = abs(float(pos['positionAmt']))
        
        if cantidad > 0:
            # Si estamos en Long (positivo), vendemos. Si estamos en Short (negativo), compramos.
            lado_cierre = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
            client.futures_create_order(symbol=SIMBOLO, side=lado_cierre, type='MARKET', quantity=cantidad)
            print(f"💰 CIERRE {tipo_posicion}: {cantidad} ETH | Motivo: {motivo}")
            en_posicion = False
            tipo_posicion = None
            return True
    except Exception as e:
        print(f"❌ Error al cerrar: {e}")
    return False

def main_loop():
    global en_posicion, tipo_posicion
    print(f"🚀 {NOMBRE_BOT} - ATAQUE BI-DIRECCIONAL ACTIVADO")
    
    while True:
        p, p_di, m_di, adx, cap, ema = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            fuerza_emoji = "🐂" if p_di > m_di else "🐻"
            
            if not en_posicion:
                print(f"🔎 [{hora}] {fuerza_emoji} | ADX: {adx:.1f} | P: {p:.1f} | EMA: {ema:.1f}")
                
                # --- ENTRADA EN LONG (EL MERCADO SUBE) ---
                if p > (ema + DISTANCIA_EMA) and adx >= ADX_ENTRADA and p_di > m_di:
                    cantidad = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad)
                    print(f"🔥 ENTRADA LONG: {cantidad} ETH a {p} | Cap: ${cap:.2f}")
                    en_posicion = True
                    tipo_posicion = 'LONG'

                # --- ENTRADA EN SHORT (EL MERCADO CAE) ---
                elif p < (ema - DISTANCIA_EMA) and adx >= ADX_ENTRADA and m_di > p_di:
                    cantidad = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=cantidad)
                    print(f"📉 ENTRADA SHORT: {cantidad} ETH a {p} | Cap: ${cap:.2f}")
                    en_posicion = True
                    tipo_posicion = 'SHORT'
            
            else:
                # --- GESTIÓN DE SALIDAS INTELIGENTES ---
                umbral_salida = ADX_SALIDA_SNIPER if adx > 32 else ADX_SALIDA_BASE
                
                if tipo_posicion == 'LONG':
                    print(f"👀 [LONG] {fuerza_emoji} | P: {p:.1f} | ADX: {adx:.1f} | Piso: {umbral_salida}")
                    if adx < umbral_salida or p < (ema * 0.998) or (m_di > p_di and m_di > 30):
                        cerrar_posicion("Salida de Long (Cambio de fuerza)")
                
                elif tipo_posicion == 'SHORT':
                    print(f"👀 [SHORT] {fuerza_emoji} | P: {p:.1f} | ADX: {adx:.1f} | Piso: {umbral_salida}")
                    if adx < umbral_salida or p > (ema * 1.002) or (p_di > m_di and p_di > 30):
                        cerrar_posicion("Salida de Short (Cambio de fuerza)")
            
            sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    if app:
        Thread(target=run_web, daemon=True).start()
    main_loop()
