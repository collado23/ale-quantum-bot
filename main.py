import requests, time, hmac, hashlib, threading
from flask import Flask

# --- CONFIGURACIÓN MAESTRA ---
API_KEY = "NDOpSIfLlXENmHGEDJWUPnFacHLTs15iKGxjaSt7ubkqWEOjQ2MF9gJEOz1U5lIW"
API_SECRET = "ogV8joih6ZTKMv7NNz55xyneZQttgv4NQjOsgGqpsDZkL2s7mhPz9LixZosu3AyQ"
BASE_URL = "https://fapi.binance.com"
SYMBOL = "ETHUSDT"

app = Flask('')
@app.route('/')
def home(): return "🔱 QUANTUM V4: RADAR 200 + TRAILING MANUAL ACTIVO"

# --- FUNCIONES DE SEGURIDAD Y FIRMA ---
def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def enviar_orden(side, qty):
    ts = int(time.time() * 1000)
    query = f"symbol={SYMBOL}&side={side}&type=MARKET&quantity={qty}&timestamp={ts}"
    signature = firmar(query)
    url = f"{BASE_URL}/fapi/v1/order?{query}&signature={signature}"
    res = requests.post(url, headers={"X-MBX-APIKEY": API_KEY}).json()
    return res

# --- RADAR DE PROFUNDIDAD (200 NIVELES) ---
def obtener_radar_200():
    url = f"{BASE_URL}/fapi/v1/depth?symbol={SYMBOL}&limit=500"
    res = requests.get(url).json()
    vol_compra = sum(float(bid[1]) for bid in res['bids'][:200])
    vol_venta = sum(float(ask[1]) for ask in res['asks'][:200])
    total = vol_compra + vol_venta
    return (vol_compra / total) * 100

def obtener_precio():
    url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={SYMBOL}"
    return float(requests.get(url).json()['price'])

def obtener_saldo():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    url = f"{BASE_URL}/fapi/v2/balance?{q}&signature={firmar(q)}"
    res = requests.get(url, headers={"X-MBX-APIKEY": API_KEY}).json()
    return next((float(i['balance']) for i in res if i['asset'] == 'USDT'), 0)

# --- LÓGICA DEL TRAILING STOP POR SOFTWARE ---
def ejecutar_operacion(side, qty):
    print(f"🚀 DISPARANDO {side}...", flush=True)
    orden = enviar_orden(side, qty)
    if 'orderId' not in orden:
        print(f"❌ Error al abrir orden: {orden}", flush=True)
        return

    precio_entrada = obtener_precio()
    mejor_precio = precio_entrada
    lado_cierre = "SELL" if side == "BUY" else "BUY"
    
    # Bucle de Trailing Stop Dinámico (0.3% de retroceso)
    while True:
        precio_actual = obtener_precio()
        
        if side == "BUY":
            if precio_actual > mejor_precio: mejor_precio = precio_actual
            retroceso = (mejor_precio - precio_actual) / mejor_precio * 100
            if retroceso > 0.3: # Si el precio cae 0.3% desde el pico, cerramos
                print(f"⚠️ REBOTE DETECTADO. Cerrando Ganancia...", flush=True)
                enviar_orden(lado_cierre, qty)
                break
        else:
            if precio_actual < mejor_precio: mejor_precio = precio_actual
            retroceso = (precio_actual - mejor_precio) / mejor_precio * 100
            if retroceso > 0.3: # Si el precio sube 0.3% desde el fondo, cerramos
                print(f"⚠️ REBOTE DETECTADO. Cerrando Ganancia...", flush=True)
                enviar_orden(lado_cierre, qty)
                break
        time.sleep(1)

def iniciar_bot():
    print("🚄 TREN BALA V4 INICIADO. Radar 200 y Trailing Manual...", flush=True)
    while True:
        try:
            saldo = obtener_saldo()
            p_suba = obtener_radar_200()
            precio_act = obtener_precio()
            
            # Cálculo de cantidad con interés compuesto (20% del saldo x10 apalancamiento)
            cantidad_eth = round((saldo * 0.20 * 10) / precio_act, 3)
            
            print(f"📊 Saldo: ${saldo:.2f} | 🔮 Suba: {p_suba:.1f}% | Baja: {100-p_suba:.1f}%", flush=True)

            if p_suba > 75: # Muro de compra masivo
                ejecutar_operacion("BUY", cantidad_eth)
            elif p_suba < 25: # Muro de venta masivo
                ejecutar_operacion("SELL", cantidad_eth)
            
            time.sleep(30)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=iniciar_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
