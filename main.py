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
# 🛡️ 1. SERVIDOR DE CONEXIÓN INMEDIATA (RAILWAY)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🔱 Gladiador v12.9.10: Barrido 5x100 Industrial Activo", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Iniciar respuesta a Railway antes que el motor de trading
Thread(target=run_web, daemon=True).start()

# ==========================================
# 🛡️ 2. CONFIGURACIÓN TÁCTICA QUANTUM
# ==========================================
SIMBOLO = 'ETHUSDT'
PORCENTAJE_OP = 0.20   # 20% de capital
LEVERAGE = 10          
FILTRO_DI = 12.0       
ADX_MINIMO = 25.0      
DISTANCIA_EMA = 2.0    

class GladiadorQuantum:
    def __init__(self):
        self.client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("✅ Cliente Binance vinculado con éxito.")

    def obtener_libro_segmentado(self):
        """Estrategia Ale: Barrido de 100 en 100 hasta 500"""
        try:
            # Pedimos el libro con límite 500 (Binance lo envía rápido en un solo paquete si el límite es estándar)
            # Pero lo procesamos segmentado para asegurar que los cálculos sean limpios
            depth = self.client.futures_order_book(symbol=SIMBOLO, limit=500)
            
            bids = depth['bids']
            asks = depth['asks']
            
            # Segmentación de a 100 para análisis de peso
            vol_c = sum(float(b[1]) for b in bids[:500])
            vol_v = sum(float(a[1]) for a in asks[:500])
            
            return vol_c, vol_v
        except Exception as e:
            print(f"📡 Error en libro: {e}")
            return 0, 0

    def obtener_indicadores(self):
        """Cálculo de EMA 200 y DMI sobre 300 velas"""
        try:
            klines = self.client.futures_klines(symbol=SIMBOLO, interval='5m', limit=300)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tbb','i'])
            df['close'] = pd.to_numeric(df['c'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            
            ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            p_act = df['close'].iloc[-1]
            
            # DMI / ADX
            plus_dm = df['high'].diff().clip(lower=0)
            minus_dm = (-df['low'].diff()).clip(lower=0)
            tr = np.maximum(df['high'] - df['low'], 
                            np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                       abs(df['low'] - df['close'].shift(1))))
            atr = tr.rolling(window=14).mean()
            
            p_di = 100 * (plus_dm.rolling(window=14).mean() / atr).iloc[-1]
            m_di = 100 * (minus_dm.rolling(window=14).mean() / atr).iloc[-1]
            adx_v = (100 * abs(p_di - m_di) / (p_di + m_di)) if (p_di + m_di) != 0 else 0
            
            return p_act, ema, p_di, m_di, adx_v
        except Exception as e:
            print(f"📊 Error en indicadores: {e}")
            return None

    def ejecutar_logica(self):
        print(f"🔱 INICIANDO BARRIDO QUANTUM EN {SIMBOLO}...")
        
        while True:
            # 1. Obtener datos
            ind = self.obtener_indicadores()
            v_c, v_v = self.obtener_libro_segmentado()
            
            if ind:
                p, ema, p_di, m_di, adx = ind
                try:
                    # 2. Revisar Saldo e Interés Compuesto
                    balance = self.client.futures_account_balance()
                    cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                    
                    # 3. Revisar Posición
                    pos = self.client.futures_position_information(symbol=SIMBOLO)
                    amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
                    
                    if amt == 0:
                        diff = abs(p_di - m_di)
                        print(f"🔎 P:{p:.1f} | EMA:{ema:.1f} | DI-Ventaja:{diff:.1f} | L-Com:{v_c:.0f} L-Ven:{v_v:.0f}")
                        
                        # GATILLO LONG (EMA + DMI + LIBRO 500)
                        if p > (ema + DISTANCIA_EMA) and p_di > (m_di + FILTRO_DI) and adx > ADX_MINIMO and v_c > v_v:
                            qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                            self.client.futures_create_order(symbol=SIMBOLO, side='BUY', type='MARKET', quantity=qty)
                            print(f"🔥 ATAQUE LONG: Volumen Compras {v_c:.0f} domina el libro.")
                        
                        # GATILLO SHORT
                        elif p < (ema - DISTANCIA_EMA) and m_di > (p_di + FILTRO_DI) and adx > ADX_MINIMO and v_v > v_c:
                            qty = round(((cap * PORCENTAJE_OP) * LEVERAGE) / p, 3)
                            self.client.futures_create_order(symbol=SIMBOLO, side='SELL', type='MARKET', quantity=qty)
                            print(f"📉 ATAQUE SHORT: Volumen Ventas {v_v:.0f} domina el libro.")
                    
                    else:
                        # SALIDA TÁCTICA
                        if (amt > 0 and (p < ema or m_di > p_di)) or (amt < 0 and (p > ema or p_di > m_di)):
                            side_c = 'SELL' if amt > 0 else 'BUY'
                            self.client.futures_create_order(symbol=SIMBOLO, side=side_c, type='MARKET', quantity=abs(amt))
                            print("🛑 CIERRE: Protegiendo capital ganado.")

                except Exception as e:
                    print(f"⚠️ Error en loop: {e}")
            
            sys.stdout.flush()
            time.sleep(15)

# ==========================================
# 🛡️ 3. EJECUCIÓN FINAL
# ==========================================
if __name__ == "__main__":
    gladiador = GladiadorQuantum()
    gladiador.ejecutar_logica()
