import os, time, pandas as pd, numpy as np  
import yfinance as yf
from binance.client import Client

# --- CONEXIÓN ---
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
client = Client(API_KEY, API_SECRET)

SIMBOLO = "ETHUSDT"
CANTIDAD = 0.05 
APALANCAMIENTO = 10

def descargar_memoria_adn():
    print("📡 Descargando ADN de 4 años para ETH (Yahoo Finance)...")
    try:
        # Descargamos 5 años para tener 4 años limpios con EMA 200
        data = yf.download("ETH-USD", period="5y", interval="1d", progress=False)
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        df = data.copy()
        df['ema'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['dist'] = ((df['Close'] - df['ema']) / df['ema']) * 100
        
        # Guardamos en una variable global para que el bot la consulte
        memoria = df[abs(df['dist']) > 1.8].copy()
        print(f"✅ ADN Cargado: {len(memoria)} patrones detectados.")
        return memoria
    except Exception as e:
        print(f"⚠️ Error al bajar ADN: {e}")
        return pd.DataFrame()

# CARGAMOS EL ADN AL ARRANCAR
MEMORIA_HISTORICA = descargar_memoria_adn()

def ejecutar_quantum_capital():
    print(f"🔱 GLADIADOR ETH 5M (CAPITAL) - ACTIVADO")
    en_operacion = False
    p_entrada, elast_entrada, max_roi = 0, 0, 0
    acumulado_usd = 0.0

    while True:
        try:
            # Datos 5m para Ethereum
            k = client.futures_klines(symbol=SIMBOLO, interval='5m', limit=100)
            df = pd.DataFrame(k).astype(float)
            p_actual = df[4].iloc[-1]
            ema_actual = df[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_actual = ((p_actual - ema_actual) / ema_actual) * 100
            
            # --- TABLERO DE CONTROL ---
            print("\n" + "═"*45)
            print(f"💎 ETH: {p_actual:.2f} | 💵 GANANCIA HOY: ${acumulado_usd:.2f}")
            print(f"🧲 ELÁSTICO: {dist_actual:+.2f}% | 🧠 ADN: {len(MEMORIA_HISTORICA)} pts")
            
            if en_operacion:
                roi = ((p_entrada - p_actual) / p_entrada) * 100 if elast_entrada > 0 else ((p_actual - p_entrada) / p_entrada) * 100
                if roi > max_roi: max_roi = roi
                
                t_stop = 0.4 if max_roi < 3 else 1.2
                print(f"📈 ROI: {roi:+.2f}% | 🎯 PICO: {max_roi:+.2f}%")
                
                if max_roi > 0.8 and roi < (max_roi - t_stop):
                    ganancia = (CANTIDAD * p_actual) * (roi / 100)
                    acumulado_usd += ganancia
                    print(f"✅ CIERRE CAJA: +${ganancia:.2f}")
                    en_operacion = False

            # ENTRADA (Sensibilidad 1.8%)
            if not en_operacion and abs(dist_actual) >= 1.8:
                side = 'SELL' if dist_actual > 0 else 'BUY'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=CANTIDAD)
                p_entrada, elast_entrada, max_roi, en_operacion = p_actual, dist_actual, 0, True
                print(f"🔥 DISPARO CAPITAL: {side} en {dist_actual:.2f}%")

            print("═"*45)
            time.sleep(15)

        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(20)

if __name__ == "__main__":
    ejecutar_quantum_capital()
