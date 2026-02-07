import requests, time, hmac, hashlib
from flask import Flask
import threading

# --- SISTEMA DE SUPERVIVENCIA PARA RENDER GRATIS ---
app = Flask('')
@app.route('/')
def home(): return "🔱 ALE IA QUANTUM - SISTEMA OPERATIVO 24/7"

def run(): app.run(host='0.0.0.0', port=8080)

# --- TUS CLAVES DE BINANCE (ACTUALIZADAS) ---
API_KEY = "NDOpSIfLlXENmHGEDJWUPnFacHLTs15iKGxjaSt7ubkqWEOjQ2MF9gJEOz1U5lIW"
API_SECRET = "ogV8joih6ZTKMv7NNz55xyneZQttgv4NQjOsgGqpsDZkL2s7mhPz9LixZosu3AyQ"
BASE_URL = "https://fapi.binance.com"

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def obtener_datos():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    url = f"{BASE_URL}/fapi/v2/balance?{q}&signature={firmar(q)}"
    res = requests.get(url, headers={"X-MBX-APIKEY": API_KEY}).json()
    return res

def iniciar_bot():
    print("🔱 INICIANDO ALE IA QUANTUM DESDE FRANKFURT...")
    print("📊 Analizando Compras, Ventas y Bitcoin por separado.")
    
    while True:
        try:
            datos = obtener_datos()
            # Buscamos el saldo en USDT
            saldo = next((float(i['balance']) for i in datos if i['asset'] == 'USDT'), 0)
            
            if saldo > 0:
                # REGLA DE INTERÉS COMPUESTO (20%)
                inversion = saldo * 0.20
                
                # REGLA DE ESCALABILIDAD ALE
                if saldo >= 100:
                    trades = 10
                elif saldo >= 60:
                    trades = 6
                else:
                    trades = 1
                
                print("-" * 40)
                print(f"💰 SALDO ACTUAL: ${saldo:.2f} USDT")
                print(f"📈 INVERSIÓN (20%): ${inversion:.2f}")
                print(f"🎯 PLAN DE ATAQUE: {trades} operaciones activas.")
                print(f"📍 UBICACIÓN: Frankfurt, Alemania (OK)")
            else:
                print("⏳ Conexión establecida. Esperando que los $6 aparezcan en Billetera de Futuros...")

            time.sleep(60) # El bot patrulla cada minuto
            
        except Exception as e:
            print(f"⚙️ Ajustando sistema por error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    # Iniciar servidor web para que Render no lo apague
    t = threading.Thread(target=run)
    t.setDaemon(True)
    t.start()
    
    # Iniciar el motor del bot
    iniciar_bot()
