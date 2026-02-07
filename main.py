import requests, time, hmac, hashlib, threading
from flask import Flask

# --- CONFIGURACIÓN MAESTRA ---
API_KEY = "NDOpSIfLlXENmHGEDJWUPnFacHLTs15iKGxjaSt7ubkqWEOjQ2MF9gJEOz1U5lIW"
API_SECRET = "ogV8joih6ZTKMv7NNz55xyneZQttgv4NQjOsgGqpsDZkL2s7mhPz9LixZosu3AyQ"
BASE_URL = "https://fapi.binance.com"
SYMBOL = "ETHUSDT"

app = Flask('')
@app.route('/')
def home(): return "🔱 QUANTUM V4.1 - INMORTAL ACTIVO"

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def enviar_orden(side, qty):
    ts = int(time.time() * 1000)
    query = f"symbol={SYMBOL}&side={side}&type=MARKET&quantity={qty}&timestamp={ts}"
    url = f"{BASE_URL}/fapi/v1/order?{query}&signature={firmar(query)}"
    return requests.post(url, headers={"X-MBX-APIKEY": API_KEY}).json()

def obtener_datos():
    url_p = f"{BASE_URL}/fapi/v1/ticker/price?symbol={SYMBOL}"
    url_d = f"{BASE_URL}/fapi/v1/depth?symbol={SYMBOL}&limit=500"
    p = float(requests.get(url_p).json()['price'])
    res = requests.get(url_d).json()
    v_c = sum(float(b[1]) for b in res['bids'][:200])
    v_v = sum(float(a[1]) for a in res['asks'][:200])
    return p, (v_c / (v_c + v_v)) * 100

def ejecutar_operacion(side, qty):
    print(f"🚀 ENTRANDO EN {side} - Cantidad: {qty}", flush=True)
    enviar_orden(side, qty)
    p_entrada, _ = obtener_datos()
    mejor_p = p_entrada
    lado_c = "SELL" if side == "BUY" else "BUY"
    
    while True: # Bucle de Trailing Inmortal
        time.sleep(5) 
        p_act, _ = obtener_datos()
        if side == "BUY":
            if p_act > mejor_p: mejor_p = p_act
            ret = (mejor_p - p_act) / mejor_p * 100
        else:
            if p_act < mejor_p: mejor_p = p_act
            ret = (p_act - mejor_p) / mejor_p * 100
        
        # El bot "grita" cada 5 segundos para no dormirse
        print(f"📡 VIGILANDO {side} | Actual: ${p_act} | Max: ${mejor_p} | Retroceso: {ret:.2f}%", flush=True)
        
        if ret > 0.22: # Umbral de salida
            print(f"⚠️ HACHAZO DETECTADO. Cerrando posición...", flush=True)
            enviar_orden(lado_c, qty)
            break

def iniciar_bot():
    print("🚄 TREN BALA V4.1: MODO INMORTAL ACTIVADO", flush=True)
    while True:
        try:
            p_act, p_suba = obtener_datos()
            # Interés compuesto 20% x10 apalancamiento (Calculado sobre el saldo real)
            ts = int(time.time() * 1000)
            q = f"timestamp={ts}"
            res_s = requests.get(f"{BASE_URL}/fapi/v2/balance?{q}&signature={firmar(q)}", headers={"X-MBX-APIKEY": API_KEY}).json()
            saldo = next(float(i['balance']) for i in res_s if i['asset'] == 'USDT')
            
            qty = round((saldo * 0.20 * 10) / p_act, 3)
            print(f"📊 ${saldo:.2f} | 🔮 Radar: {p_suba:.1f}% Suba / {100-p_suba:.1f}% Baja", flush=True)

            if p_suba > 76: ejecutar_operacion("BUY", qty)
            elif p_suba < 24: ejecutar_operacion("SELL", qty)
            time.sleep(20)
        except: time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=iniciar_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
