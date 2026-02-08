import time, os, sys, IA_Estratega
from binance.client import Client

def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ Gladiador ETH: Conexión Exitosa")
    except: return

    while True:
        try:
            datos = IA_Estratega.analizar_mercado(client, sym)
            dec, p, adx, vol = datos[0], datos[1], datos[2], datos[3]
            
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            print(f"🔎 ETH:{p} | ADX:{round(adx,1)} | Señal:{dec} | Pos:{amt}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                # Interés compuesto 20%
                cap = next(float(b['balance']) for b in client.futures_account_balance() if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # ESCUDO DISTANCIA 9 (0.9%)
                inv = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(symbol=sym, side=inv, type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                print(f"🚀 Entrada {dec} - Escudo 0.9% Activo")

        except Exception as e: print(f"⚠️ Error: {e}")
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    ejecutar_sistema()
