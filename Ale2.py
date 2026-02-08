import time, os, sys, IA_Estratega
from binance.client import Client
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "🛡️ Online", 200
def run_flask():
    p = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=p)
Thread(target=run_flask, daemon=True).start()

def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ Conectado")
    except: return
    while True:
        try:
            dec, p, vc, vv = IA_Estratega.analizar_mercado(client, sym)
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            print(f"🔎 P:{p} | Señal: {dec}")
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3)
                client.futures_create_order(symbol=sym, side='BUY' if dec=="LONG" else 'SELL', type='MARKET', quantity=qty)
            elif amt != 0 and ((amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG")):
                client.futures_create_order(symbol=sym, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
        except: pass
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__": ejecutar_sistema()
