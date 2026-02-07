import requests, time, hmac, hashlib, os
import pandas as pd # Para calcular las EMAs rápido

# --- CONFIGURACIÓN ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"
SYMBOL = "ETHUSDT"

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def obtener_emas():
    """Calcula las 3 EMAs (35, 50, 200) usando velas de 5 minutos"""
    url = f"{BASE_URL}/fapi/v1/klines?symbol={SYMBOL}&interval=5m&limit=300"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=['ts', 'o', 'h', 'l', 'c', 'v', 'ts_end', 'q', 'n', 'v_buy', 'q_buy', 'i'])
    cierre = df['c'].astype(float)
    
    ema35 = cierre.ewm(span=35, adjust=False).mean().iloc[-1]
    ema50 = cierre.ewm(span=50, adjust=False).mean().iloc[-1]
    ema200 = cierre.ewm(span=200, adjust=False).mean().iloc[-1]
    
    return round(ema35, 2), round(ema50, 2), round(ema200, 2), cierre.iloc[-1]

def ejecutar_con_trailing_web(lado, cantidad):
    ts = int(time.time() * 1000)
    # Entrada
    q_e = f"symbol={SYMBOL}&side={lado}&type=MARKET&quantity={cantidad}&timestamp={ts}"
    requests.post(f"{BASE_URL}/fapi/v1/order?{q_e}&signature={firmar(q_e)}", headers={"X-MBX-APIKEY": API_KEY})
    # Trailing Stop Web (0.5%)
    lado_s = "SELL" if lado == "BUY" else "BUY"
    time.sleep(1.5)
    q_t = (f"symbol={SYMBOL}&side={lado_s}&type=TRAILING_STOP_MARKET"
           f"&quantity={cantidad}&callbackRate=0.5&timestamp={ts+2000}")
    requests.post(f"{BASE_URL}/fapi/v1/order?{q_t}&signature={firmar(q_t)}", headers={"X-MBX-APIKEY": API_KEY})

def radar_quantum_pro():
    print("🚀 RADAR 200 + TRIPLE EMA (35, 50, 200) ACTIVADO")
    while True:
        try:
            # 1. Análisis de EMAs
            e35, e50, e200, precio = obtener_emas()
            
            # 2. Análisis de Radar 200 Niveles
            res = requests.get(f"{BASE_URL}/fapi/v1/depth?symbol={SYMBOL}&limit=500").json()
            c_200 = sum(float(b[1]) for b in res['bids'][:200])
            v_200 = sum(float(a[1]) for a in res['asks'][:200])
            p_suba = (c_200 / (c_200 + v_200)) * 100

            # Logs súper completos
            print(f"⏱️ {time.strftime('%H:%M:%S')} | Radar: {p_suba:.1f}% | Precio: {precio}")
            print(f"📊 EMAs -> 35: {e35} | 50: {e50} | 200: {e200}")

            # LÓGICA DE HACHAZO (Radar + Tendencia)
            # Entramos si el Radar es fuerte Y el precio está arriba de la EMA 200
            if p_suba > 76 and precio > e200:
                print("🔥 TENDENCIA ALCISTA + HACHAZO RADAR. ¡Comprando!")
                # Aquí el bot calcula el 20% de tus $36.62 y ejecuta
                # ejecutar_con_trailing_web("BUY", cantidad)
                time.sleep(600)

            time.sleep(15)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    radar_quantum_pro()
