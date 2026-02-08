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
    def home(): return "Gladiador Sniper v12.3: Estabilizado"
    def run_web(): app.run(host='0.0.0.0', port=8080)
except ImportError:
    app = None

# ==========================================
# 🔱 PARÁMETROS TÁCTICOS v12.3 (ESTABILIZADO)
# ==========================================
NOMBRE_BOT = "GLADIADOR v12.3"
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # Usar 20% del capital
LEVERAGE = 10          
ADX_ENTRADA = 22.0     
ADX_SALIDA_BASE = 15.0 
ADX_SALIDA_SNIPER = 25.0 
DISTANCIA_EMA = 5.0    
en_posicion = False      

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
        
        # CÁLCULO DE FUERZAS DI+ / DI- / ADX
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = (-df['low'].diff()).clip(lower=0)
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        atr = tr.rolling(window=14).mean()
        
        p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
        m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
        dx = 100 * abs(p_di - m_di) / (p_di + m_di)
        adx_val = dx.rolling(window=14).mean().iloc[-1] # Suavizado para evitar saltos locos
        
        balance = client.futures_account_balance()
        cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
        
        return p_actual, p_di, m_di, adx_val, cap, ema200
    except Exception as e:
        print(f"📡 Sincronizando: {e}")
        return None, None, None, None, None, None

def cerrar_posicion(motivo):
    global en_posicion
    try:
        info = client.futures_position_information(symbol=SIMBOLO)
        pos = next(p for p in info if p['symbol'] == SIMBOLO)
        cantidad = abs(float(pos['positionAmt']))
        
        if cantidad > 0:
            side_salida = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
            client.futures_create_order(symbol=SIMBOLO, side=side_salida, type='MARKET', quantity=cantidad)
            print(f"💰 CIERRE: {cantidad} ETH | Motivo: {motivo}")
            en_posicion = False
            return True
    except Exception as e:
        print(f"❌ Error al cerrar: {e}")
    return False

def main_loop():
    global en_posicion
    print(f"🚀 {NOMBRE_BOT} - ACTIVADO")
    
    while True:
        p, p_di, m_di, adx, cap, ema = obtener_datos()
        
        if p is not None:
            hora = time.strftime('%H:%M:%S')
            fuerza_emoji = "🐂" if p_di > m_di else "🐻"
            distancia = p - ema
            
            if not en_posicion:
                print(f"🔎 [{hora}] {fuerza_emoji} | ADX: {adx:.1f} | P: {p:.1f} | EMA: {ema:.1f}")
                # Entrada con filtro de distancia y fuerza mínima
                if p > (ema + DISTANCIA_EMA) and adx >= ADX_ENTRADA and p_di > m_di:
                    margen = cap * PORCENTAJE_OP
                    cantidad = round((margen * LEVERAGE) / p, 3)
                    client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=cantidad)
                    print(f"🔥 ENTRADA: {cantidad} ETH a {p} | Cap: ${cap:.2f}")
                    en_posicion = True
            
            else:
                # --- LÓGICA DE SALIDA v12.3 (MÁS AGUANTE) ---
                umbral_salida = ADX_SALIDA_SNIPER if adx > 32 else ADX_SALIDA_BASE
                
                print(f"👀 [{hora}] {fuerza_emoji} | P: {p:.1f} | ADX: {adx:.1f} | -DI: {m_di:.1f}")
                
                # 1. Salida por debilidad de tendencia
                if adx < umbral_salida:
                    cerrar_posicion(f"Agotamiento (ADX: {adx:.1f})")
                
                # 2. Salida por ruptura de suelo (EMA 200 con colchón 0.2%)
                elif p < (ema * 0.998):
                    cerrar_posicion("Ruptura de suelo EMA")
                
                # 3. Hachazo Sniper Estabilizado: Solo si el oso es realmente FUERTE
                # No cerramos solo por un cruce, pedimos que el -DI supere 30
                elif m_di > p_di and m_di > 30 and adx < 35:
                    cerrar_posicion("Hachazo Sniper: Fuerza vendedora confirmada")
            
            sys.stdout.flush()
        
        # Revisión cada 30 segundos (Equilibrio entre velocidad y comisiones)
        time.sleep(30)

if __name__ == "__main__":
    if app:
        Thread(target=run_web, daemon=True).start()
    main_loop()
