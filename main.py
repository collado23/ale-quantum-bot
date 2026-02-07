import requests, time, hmac, hashlib, os
import pandas as pd
import numpy as np

# --- CONFIGURACIÓN DE ALE ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"
SYMBOL = "ETHUSDT"
ADX_MINIMO = 24.0      # Solo entra con tendencia fuerte
DISTANCIA_MIN = 4.0    # Distancia mínima al EMA 200
LEVERAGE = 10
MARGEN_USO = 0.20      # 20% de interés compuesto

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def calcular_adx(df, periods=14):
    """Calcula el ADX sin librerías externas"""
    df = df.copy()
    df['h-l'] = df['h'] - df['l']
    df['h-pc'] = abs(df['h'] - df['c'].shift(1))
    df['l-pc'] = abs(df['l'] - df['c'].shift(1))
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    
    df['+dm'] = np.where((df['h'] - df['h'].shift(1)) > (df['l'].shift(1) - df['l']), 
                         pmax(df['h'] - df['h'].shift(1), 0), 0)
    df['-dm'] = np.where((df['l'].shift(1) - df['l']) > (df['h'] - df['h'].shift(1)), 
                         pmax(df['l'].shift(1) - df['l'], 0), 0)
    
    tr_smooth = df['tr'].rolling(window=periods).mean()
    dm_pos_smooth = df['+dm'].rolling(window=periods).mean()
    dm_neg_smooth = df['-dm'].rolling(window=periods).mean()
    
    di_pos = 100 * (dm_pos_smooth / tr_smooth)
    di_neg = 100 * (dm_neg_smooth / tr_smooth)
    dx = 100 * abs(di_pos - di_neg) / (di_pos + di_neg)
    adx = dx.rolling(window=periods).mean()
    return adx.iloc[-1]

def pmax(a, b): return np.where(a > b, a, b)

def obtener_indicadores():
    url = f"{BASE_URL}/fapi/v1/klines?symbol={SYMBOL}&interval=5m&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=['ts','o','h','l','c','v','te','q','n','v_buy','q_buy','i'])
    df[['h','l','c']] = df[['h','l','c']].astype(float)
    
    ema200 = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
    adx_val = calcular_adx(df)
    precio_act = df['c'].iloc[-1]
    distancia = abs(precio_act - ema200)
    
    return round(ema200, 2), round(adx_val, 2), round(distancia, 2), precio_act

def en_posicion():
    ts = int(time.time() * 1000)
    q = f"symbol={SYMBOL}&timestamp={ts}"
    res = requests.get(f"{BASE_URL}/fapi/v2/positionRisk?{q}&signature={firmar(q)}", headers={"X-MBX-APIKEY": API_KEY}).json()
    return abs(float(res[0]['positionAmt'])) > 0

def quantum_final_ale():
    print(f"🚀 GATITO QUANTUM | ADX: {ADX_MINIMO} | DIST: {DISTANCIA_MIN}")
    estado_anterior = False

    while True:
        try:
            pos_actual = en_posicion()
            if estado_anterior and not pos_actual:
                print("⚗️ BREAKING BAD: ¡Operación cerrada! Preparando siguiente tanda.")
            estado_anterior = pos_actual

            if not pos_actual:
                ema200, adx, dist, precio = obtener_indicadores()
                
                # Radar 200 niveles
                res_l = requests.get(f"{BASE_URL}/fapi/v1/depth?symbol={SYMBOL}&limit=500").json()
                c_200 = sum(float(b[1]) for b in res_l['bids'][:200])
                v_200 = sum(float(a[1]) for a in res_l['asks'][:200])
                p_suba = (c_200 / (c_200 + v_200)) * 100

                print(f"⏱️ {time.strftime('%H:%M:%S')} | Radar: {p_suba:.1f}% | ADX: {adx} | Dist: {dist}")

                if p_suba > 76 and adx > ADX_MINIMO and dist > DISTANCIA_MIN and precio > ema200:
                    print(f"🔥 HACHAZO: Radar {p_suba:.1f}% + ADX {adx} + Dist {dist}. ¡ADENTRO!")
                    # Aquí el bot manda la orden con interés compuesto y Trailing Web
                    time.sleep(600)

            time.sleep(15)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    quantum_final_ale()
