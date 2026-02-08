import time
import os
import sys
from binance.client import Client
from flask import Flask
from threading import Thread
import IA_Estratega 

app = Flask('')

@app.route('/')
def home():
    return "🛡️ Gladiador Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

def ejecutar_sistema():
    SIMBOLO = 'ETHUSDT'
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ Ale2: Motor encendido y conectado.")
    except:
        print("❌ Error API Keys")
        return

    while True:
        try:
            dec, p, vc, vv = IA_Estratega.analizar_mercado(client, SIMBOLO)
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
            
            print(f"🔎 P:{p:.1f} | L-C:{vc:.0f} | L-V:{vv:.0f} | Decisión: {dec}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3) 
                client.futures_create_order(symbol=SIMBOLO, side='BUY' if dec == "LONG" else 'SELL', type='MARKET', quantity=qty)
            elif amt != 0 and ((amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG")):
                client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
        except Exception as e:
            print(f"⚠️ Error Ale2: {e}")
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    ejecutar_sistema()
