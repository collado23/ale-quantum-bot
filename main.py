import requests, time, hmac, hashlib, os

# Configuración
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"

def hachazo_cierre_web(simbolo, lado, cantidad):
    # Esta es la orden rápida que hablamos para que no se tilde
    timestamp = int(time.time() * 1000)
    query = f"symbol={simbolo}&side={lado}&type=MARKET&quantity={cantidad}&timestamp={timestamp}"
    firma = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    requests.post(f"{BASE_URL}/fapi/v1/order?{query}&signature={firma}", headers={"X-MBX-APIKEY": API_KEY})
    print("🎯 ¡HACHAZO DE CIERRE EJECUTADO!")

def loop_trailing_dinamico(precio_entrada, lado, cantidad):
    precio_maximo = precio_entrada
    distancia = 0.005 # 0.5% dinámico
    print(f"🕵️ Vigilando Trailing Dinámico para {lado}...")

    while True:
        try:
            # Pedimos el precio actual por fuera para que no se tilde el bot
            res = requests.get(f"{BASE_URL}/fapi/v1/ticker/price?symbol=ETHUSDT").json()
            precio_actual = float(res['price'])

            if lado == "BUY":
                if precio_actual > precio_maximo:
                    precio_maximo = precio_actual # El stop sube
                # Si cae 0.5% del máximo... ¡Cierra!
                if precio_actual <= precio_maximo * (1 - distancia):
                    hachazo_cierre_web("ETHUSDT", "SELL", cantidad)
                    break
            
            # (Lo mismo para SHORT si lo usas)
            
            time.sleep(0.5) # Monitoreo ultra rápido
        except:
            time.sleep(1)

print("🚀 RADAR 200 + TRAILING DINÁMICO ACTIVO")
while True:
    # Aquí tu Radar 200 que analiza Compras y Ventas por separado
    # ... (Si el Radar da > 76%, llama a loop_trailing_dinamico)
    time.sleep(15)
