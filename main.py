import requests, time, hmac, hashlib, os
import pandas as pd
import numpy as np

# --- CONFIGURACIÓN ALE IA QUANTUM ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"
SYMBOL = "ETHUSDT"

# TUS PARÁMETROS BLINDADOS
ADX_MIN = 24.0      
DISTANCIA_MIN = 5.0    
MARGEN_USO = 0.20   # Interés Compuesto 20%
LEVERAGE = 10

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def obtener_datos_maestros():
    url = f"{BASE_URL}/fapi/v1/klines?symbol={SYMBOL}&interval=5m&limit=100"
    df = pd.DataFrame(requests.get(url).json(), columns=['ts','o','h','l','c','v','te','q','n','v_buy','q_buy','i'])
    df[['h','l','c']] = df[['h','l','c']].astype(float)
    
    ema200 = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
    
    # Cálculo manual de ADX con Pendiente
    def get_adx(data):
        d = data.copy()
        d['h-l'], d['h-pc'], d['l-pc'] = d['h']-d['l'], abs(d['h']-d['c'].shift(1)), abs(d['l']-d['c'].shift(1))
        d['tr'] = d[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        d['+dm'] = np.where((d['h']-d['h'].shift(1)) > (d['l'].shift(1)-d['l']), np.maximum(d['h']-d['h'].shift(1), 0), 0)
        d['-dm'] = np.where((d['l'].shift(1)-d['l']) > (d['h']-d['h'].shift(1)), np.maximum(d['l'].shift(1)-d['l'], 0), 0)
        tr_s, dp_s, dn_s = d['tr'].rolling(14).mean(), d['+dm'].rolling(14).mean(), d['-dm'].rolling(14).mean()
        dx = 100 * abs((dp_s/tr_s)-(dn_s/tr_s)) / ((dp_s/tr_s)+(dn_s/tr_s))
        return dx.rolling(14).mean()

    adx_serie = get_adx(df)
    adx_act, adx_prev = adx_serie.iloc[-1], adx_serie.iloc[-2]
    
    precio = df['c'].iloc[-1]
    distancia = precio - ema200 
    
    return round(ema200,2), round(adx_act,2), adx_act > adx_prev, round(distancia,2), precio

def quantum_v6_final():
    print(f"🔱 ALE IA QUANTUM v6 ACTIVADO | Meta 100 Op | ADX: {ADX_MIN}")
    prev_pos = False

    while True:
        try:
            ts = int(time.time()*1000)
            # Obtener Saldo USDT
            q_acc = f"timestamp={ts}"
            acc = requests.get(f"{BASE_URL}/fapi/v2/account?{q_acc}&signature={firmar(q_acc)}", headers={"X-MBX-APIKEY":API_KEY}).json()
            balance = round(float([a['walletBalance'] for a in acc['assets'] if a['asset']=='USDT'][0]), 2)
            
            # Check Posición
            q_pos = f"symbol={SYMBOL}&timestamp={ts}"
            pos = requests.get(f"{BASE_URL}/fapi/v2/positionRisk?{q_pos}&signature={firmar(q_pos)}", headers={"X-MBX-APIKEY":API_KEY}).json()
            en_op = abs(float(pos[0]['positionAmt'])) > 0

            # Aviso BREAKING BAD
            if prev_pos and not en_op:
                print(f"⚗️ BREAKING BAD: ¡Hachazo cobrado! Nuevo Saldo: ${balance}")
            prev_pos = en_op

            if not en_op:
                e200, adx, subiendo, dist, precio = obtener_datos_maestros()
                
                # Radar Quantum 200 niveles
                res_l = requests.get(f"{BASE_URL}/fapi/v1/depth?symbol={SYMBOL}&limit=500").json()
                bids = sum(float(b[1]) for b in res_l['bids'][:200])
                asks = sum(float(a[1]) for a in res_l['asks'][:200])
                radar = (bids / (bids + asks)) * 100

                flecita = "📈" if subiendo else "📉"
                print(f"⏱️ {time.strftime('%H:%M:%S')} | 💰 ${balance} | Radar: {radar:.1f}% | ADX: {adx} {flecita} | Dist: {dist}")

                # --- LÓGICA DE HACHAZO BIDIRECCIONAL ---
                
                # LONG (Suba)
                if radar > 76 and adx > ADX_MIN and subiendo and dist > DISTANCIA_MIN:
                    print(f"🔥 HACHAZO LONG: Usando ${round(balance*MARGEN_USO, 2)} | Radar {radar:.1f}%")
                    time.sleep(600) # Simula espera de ejecución web
                
                # SHORT (Baja)
                elif radar < 24 and adx > ADX_MIN and subiendo and dist < -DISTANCIA_MIN:
                    print(f"❄️ HACHAZO SHORT: Usando ${round(balance*MARGEN_USO, 2)} | Radar {radar:.1f}%")
                    time.sleep(600)

            time.sleep(15)
        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(10)

if __name__ == "__main__":
    quantum_v6_final()
