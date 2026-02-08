import time, os, sys, IA_Estratega
from binance.client import Client
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "🛡️ Gladiador Online", 200

def run_flask():
    try:
        p = int(os.environ.get("PORT", 8080))
        app.run(host='0.0.0.0', port=p)
    except: pass

# El servidor arranca PRIMERO
t = Thread(target=run_flask)
t.daemon = True
t.start()

def ejecutar_sistema():
    print("⚔️ Iniciando motor...")
    sym = 'ETHUSDT'
    try:
        # Si no tenés las API KEYS en Railway, esto va a fallar
        api = os.getenv('API_KEY')
        sec = os.getenv('API_SECRET')
        client = Client(api, sec)
        print("✅ Conexión Binance OK")
    except Exception as e:
        print(f"❌ Error API: {e}")
        return

    while True:
        try:
            dec, p, vc, vv = IA_Estratega.analizar_mercado(client, sym)
            print(f"🔎 ETH: {p} | Señal: {dec}")
            # El resto de tu lógica de órdenes sigue igual...
        except Exception as e:
            print(f"⚠️ Reintentando... {e}")
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    ejecutar_sistema()
