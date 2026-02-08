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

# Lanzar servidor de vida en un hilo aparte
Thread(target=run_flask, daemon=True).start()

def ejecutar_sistema():
    SIMBOLO = 'ETHUSDT'
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ Ale2: Conexión con Binance establecida.")
    except:
        print("❌ Error: Llaves API no encontradas.")
        return

    while True:
        try:
            # Consultamos al Cerebro
            dec, p, vc, vv = IA_Estratega.analizar_mercado(client, SIMBOLO)
            
            # Revisar posición actual
            pos = client.futures_position_information(symbol=SIMBOLO)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == SIMBOLO)
            
            if p > 0:
                print(f"🔎 P:{p:.1f} | L-C:{vc:.0f} | L-V:{vv:.0f} | Señal: {dec}")

            # Lógica de Ejecución con Interés Compuesto (20%)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                balance = client.futures_account_balance()
                cap = next(float(b['balance']) for b in balance if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3) 
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=SIMBOLO, side=side, type='MARKET', quantity=qty)
                print(f"🔥 ¡ATAQUE {side}! Cantidad: {qty}")

            elif amt != 0:
                if (amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG"):
                    client.futures_create_order(symbol=SIMBOLO, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    print("🛑 Cerrando posición por cambio de señal.")

        except Exception as e:
            print(f"⚠️ Alerta: {e}")
        
        sys.stdout.flush()
        time.sleep(15) # Descanso estratégico para Railway
