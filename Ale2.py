import time, os, sys, IA_Estratega
from binance.client import Client
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "🛡️ Gladiador ETH Online", 200
def run_flask():
    p = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=p)
Thread(target=run_flask, daemon=True).start()

def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print(f"⚔️ Gladiador ETH Conectado")
    except: return

    while True:
        try:
            dec, p, vc, vv = IA_Estratega.analizar_mercado(client, sym)
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            print(f"🔎 ETH:{p} | Señal:{dec} | Pos:{amt}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                # 1. Orden de Entrada (20% Capital x10)
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # 2. Trailing Stop Web (El que corre con el precio)
                inv_side = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=sym, 
                    side=inv_side, 
                    type='TRAILING_STOP_MARKET', 
                    callbackRate=0.5, 
                    quantity=qty, 
                    reduceOnly=True
                )
                print(f"🚀 {side} ejecutado con Trailing 0.5%")

            elif amt != 0 and ((amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG")):
                client.futures_cancel_all_open_orders(symbol=sym)
                client.futures_create_order(symbol=sym, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                print("🛑 Cambio de tendencia: Cierre total")

        except Exception as e: print(f"⚠️ Reintentando: {e}")
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__": ejecutar_sistema()
