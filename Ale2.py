import time, os, sys
import pandas as pd
import numpy as np
from binance.client import Client

# CONFIGURACIÓN
symbol = 'ETHUSDT'

def ejecutar():
    print("🚀 GLADIADOR ALE-V5: ARRANQUE RELÁMPAGO")
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ MOTOR CONECTADO")
    except Exception as e:
        print(f"❌ Error API: {e}"); return

    while True:
        try:
            # 1. DATOS (Mínimo necesario para velocidad)
            k = client.futures_klines(symbol=symbol, interval='5m', limit=300)
            df = pd.DataFrame(k)
            df = df.iloc[:, :6]
            df.columns = ['t','o','h','l','c','v']
            df = df.astype(float)

            # 2. CÁLCULOS (EMA 200 y ADX)
            p_act = df['c'].iloc[-1]
            ema = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
            dist = p_act - ema
            
            # ADX Profesional Simplificado
            up = df['h'].diff(); down = -df['l'].diff()
            p_dm = up.where((up > down) & (up > 0), 0).rolling(14).mean()
            m_dm = down.where((down > up) & (down > 0), 0).rolling(14).mean()
            tr = np.maximum(df['h']-df['l'], np.maximum(abs(df['h']-df['c'].shift(1)), abs(df['l']-df['c'].shift(1)))).rolling(14).mean()
            p_di = 100 * (p_dm / tr).iloc[-1]
            m_di = 100 * (m_dm / tr).iloc[-1]
            adx = 100 * abs(p_di - m_di) / (p_di + m_di)

            # 3. CAPITAL Y POSICIÓN (Modo ultra-ligero)
            bal = client.futures_account_balance()
            cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
            pos = client.futures_position_information(symbol=symbol)
            amt = float(pos[0]['positionAmt'])

            # 4. LÓGICA ALE (ADX 26 | DIST 9)
            dec = "ESPERAR"
            if adx > 26 and abs(dist) > 9:
                if p_act > ema and p_di > m_di: dec = "LONG"
                elif p_act < ema and m_di > p_di: dec = "SHORT"

            # 🔱 EL TABLERO QUE BUSCABAS
            print(f"🔎 ETH: {p_act} | ADX: {round(adx,1)} | Dist: {round(dist,1)} | Cap: {round(cap,2)} | {dec}")

            # 5. EJECUCIÓN (20% Compuesto x10)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                qty = round(((cap * 0.20) * 10) / p_act, 3)
                if qty < 0.001: qty = 0.001
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                
                time.sleep(2)
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=symbol, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🔥 DISPARO: {dec}")

        except Exception as e:
            print(f"📡 Aviso: {e}")
            time.sleep(10)
        
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    ejecutar()
