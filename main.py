import requests, time, hmac, hashlib, os

# Railway lee las variables que cargaste antes
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"

def obtener_datos_radar():
    try:
        # Analizamos profundidad de 200 niveles
        res = requests.get(f"{BASE_URL}/fapi/v1/depth?symbol=ETHUSDT&limit=500").json()
        bids = sum(float(b[1]) for b in res['bids'][:200]) # Compras
        asks = sum(float(a[1]) for a in res['asks'][:200]) # Ventas
        return (bids / (bids + asks)) * 100, bids, asks
    except: return 50, 0, 0

print("🚄 TREN BALA V4.2 - RAILWAY EDITION")
print("🔥 ANALIZANDO ETH CON RADAR DE 200 NIVELES...")

while True:
    try:
        porcentaje, compras, ventas = obtener_datos_radar()
        
        # Este Log lo verás en la pestaña "Logs" de Railway
        print(f"⏱️ {time.strftime('%H:%M:%S')} | Radar: {porcentaje:.1f}% | C: {compras:.0f} | V: {ventas:.0f}", flush=True)

        # Lógica de Interés Compuesto (20% de tus $36.62 x10)
        # Aquí irá la función de enviar_orden que ya tenemos perfeccionada
        
        time.sleep(15) # Escaneo constante cada 15 seg
    except Exception as e:
        print(f"Buscando señal: {e}", flush=True)
        time.sleep(10)
