import requests, time, hmac, hashlib
from flask import Flask
import threading

# --- TUS CLAVES DE BINANCE ---
API_KEY = "NDOpSIfLlXENmHGEDJWUPnFacHLTs15iKGxjaSt7ubkqWEOjQ2MF9gJEOz1U5lIW"
API_SECRET = "ogV8joih6ZTKMv7NNz55xyneZQttgv4NQjOsgGqpsDZkL2s7mhPz9LixZosu3AyQ"
BASE_URL = "https://fapi.binance.com"

app = Flask('')
@app.route('/')
def home(): return "🔱 BOT ACTIVO"

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def obtener_datos():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    url = f"{BASE_URL}/fapi/v2/balance?{q}&signature={firmar(q)}"
    try:
        res = requests.get(url, headers={"X-MBX-APIKEY": API_KEY}, timeout=10).json()
        return res
    except: return []

def iniciar_bot():
    print("🔱 CONECTANDO ALE IA QUANTUM...")
    while True:
        datos = obtener_datos()
        # Buscamos saldo en Futuros USDT
        saldo = next((float(i['balance']) for i in datos if i.get('asset') == 'USDT'), None)
        
        if saldo is not None:
            inversion = saldo * 0.20
            print("-" * 30)
            print(f"💰 SALDO EN FUTUROS: ${saldo:.2f} USDT")
            print(f"📈 PROXIMA INVERSION: ${inversion:.2f}")
            print("🚀 ESTADO: PATRULLANDO MERCADO")
            print("-" * 30)
        else:
            print("❌ ERROR: No se detecta saldo en FUTUROS. ¿Pasaste los $6 a la billetera de Futuros?")
        
        time.sleep(30)

if __name__ == "__main__":
    # Primero lanzamos el bot para ver el saldo YA
    threading.Thread(target=iniciar_bot, daemon=True).start()
    # Después el servidor para Render
    app.run(host='0.0.0.0', port=8080)
