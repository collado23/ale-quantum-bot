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
            # Sincronizado para recibir los 4 valores del cerebro
            dec, p, adx, vol = IA_Estratega.analizar_mercado(client, sym)
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            print(f"🔎 ETH:{p} | ADX:{round(adx,1)} | Vol:{round(vol,1)} | Señal:{dec} | Pos:{amt}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                # Interés compuesto 20% x10
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # TRAILING STOP AL 0.9% (DISTANCIA 9)
                inv_side = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=sym, side=inv_side, type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, quantity=qty, reduceOnly=True
                )
                print(f"🚀 {side} con Trailing 0.9% (Distancia 9) Activo")

            elif amt != 0 and ((amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG")):
                client.futures_cancel_all_open_orders(symbol=sym)
                client.futures_create_order(symbol=sym, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                print("🛑 Cambio de tendencia: Cierre total")

        except Exception as e: print(f"⚠️ Alerta: {e}")
        sys.stdout.flush()
        time.sleep(30)
