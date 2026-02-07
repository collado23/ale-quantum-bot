import requests, time, hmac, hashlib
from flask import Flask
import threading

# --- CONFIGURACIÓN MAESTRA ---
API_KEY = "NDOpSIfLlXENmHGEDJWUPnFacHLTs15iKGxjaSt7ubkqWEOjQ2MF9gJEOz1U5lIW"
API_SECRET = "ogV8joih6ZTKMv7NNz55xyneZQttgv4NQjOsgGqpsDZkL2s7mhPz9LixZosu3AyQ"
BASE_URL = "https://fapi.binance.com"
SYMBOL = "ETHUSDT"

app = Flask('')
@app.route('/')
def home(): return "🔱 TREN BALA INTELIGENTE ACTIVO"

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def obtener_datos():
    url = f"{BASE_URL}/fapi/v1/klines?symbol={SYMBOL}&interval=1m&limit=15"
    return requests.get(url).json()

def obtener_saldo():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    url = f"{BASE_URL}/fapi/v2/balance?{q}&signature={firmar(q)}"
    try:
        res = requests.get(url, headers={"X-MBX-APIKEY": API_KEY}).json()
        return next((float(i['balance']) for i in res if i['asset'] == 'USDT'), 0)
    except: return 0

def iniciar_bot():
    print("🚄 TREN BALA CON SENSOR ANTI-ZIGZAG INICIADO...", flush=True)
    while True:
        try:
            velas = obtener_datos()
            saldo = obtener_saldo()
            precios = [float(v[4]) for v in velas]
            
            rango = max(precios[-5:]) - min(precios[-5:])
            movimiento_porcentaje = (rango / precios[-1]) * 100
            
            v2_vol = float(velas[-1][5])
            vol_promedio = sum(float(v[5]) for v in velas[-11:-1]) / 10
            
            print(f"📊 Saldo: ${saldo:.2f} | Mov: {movimiento_porcentaje:.2f}% | Vol: {v2_vol:.0f}", flush=True)

            if movimiento_porcentaje < 0.25:
                print(f"😴 ZIGZAG DETECTADO. Protegiendo capital...", flush=True)
            elif v2_vol > (vol_promedio * 1.3):
                aceleracion = (precios[-1] - precios[-2]) / precios[-2]
                if aceleracion > 0:
                    print(f"🚀 [LONG] DISPARANDO 20% x10", flush=True)
                else:
                    print(f"📉 [SHORT] DISPARANDO 20% x10", flush=True)
            else:
                print("📡 ESPERANDO MASA CRÍTICA...", flush=True)
            time.sleep(60)
        except Exception as e:
            time.sleep(20)

if __name__ == "__main__":
    threading.Thread(target=iniciar_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
