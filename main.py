import time
import os
import sys
from binance.client import Client
from flask import Flask
from threading import Thread
import IA_Estratega  # Aquí importamos tu otro archivo

app = Flask('')

@app.route('/')
def home():
    return "🛡️ Gladiador Dual Activo (Ale2 + Estratega)", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Lanzar servidor de vida
Thread(target=run_flask, daemon=True).start()

# CONFIGURACIÓN
SIMBOLO = 'ETHUSDT'
client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))

def iniciar_bot():
    print("⚔️ Ale2: Motor de ejecución iniciado...")
    while True:
        try:
            # Llamamos al Cerebro para que analice
            decision, precio, vol_c, vol_v = IA_Estratega.analizar_mercado(client, SIMBOLO)
            
            # Revisar posición
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
            
            print(f"🔎 P:{precio:.1f} | L-C:{vol_c:.0f} | L-V:{vol_v:.0f} | Decisión: {decision}")

            if amt == 0 and decision in ["LONG", "SHORT"]:
                # Interés compuesto al 20%
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / precio, 3)
                
                side = 'BUY' if decision == "LONG" else 'SELL'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=qty)
                print(f"🔥 ¡ORDEN {side} ENVIADA!")

            elif amt != 0:
                # Cierre por señal contraria
                if (amt > 0 and decision == "SHORT") or (amt < 0 and decision == "LONG"):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("🛑 Cerrando posición.")

        except Exception as e:
            print(f"⚠️ Error en Ale2: {e}")
        
        sys.stdout.flush()
        time.sleep(20)

if __name__ == "__main__":
    iniciar_bot()
