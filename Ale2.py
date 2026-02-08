import time, os, sys, IA_Estratega
from binance.client import Client

def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        api = os.getenv('API_KEY')
        sec = os.getenv('API_SECRET')
        client = Client(api, sec)
        print("⚔️ Gladiador ETH: Conexión Exitosa")
    except Exception as e:
        print(f"❌ Error de Conexión: {e}")
        return

    while True:
        try:
            # --- LA LÍNEA MÁGICA ---
            # Guardamos todo en una lista llamada 'datos' para que no haya error de 'unpack'
            datos = IA_Estratega.analizar_mercado(client, sym)
            
            dec = datos[0]    # Señal
            p = datos[1]      # Precio
            adx = datos[2]    # ADX
            # Si el cerebro mandó volumen, lo usamos; si no, ponemos 0
            vol = datos[3] if len(datos) > 3 else 0
            
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            print(f"🔎 ETH:{p} | ADX:{round(adx,1)} | Vol:{round(vol,1)} | Señal:{dec} | Pos:{amt}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # TU DISTANCIA DE 9 (0.9%)
                inv_side = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=sym, side=inv_side, type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, quantity=qty, reduceOnly=True
                )
                print(f"🚀 {side} con Trailing 0.9% (Distancia 9)")

            elif amt != 0 and ((amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG")):
                client.futures_cancel_all_open_orders(symbol=sym)
                client.futures_create_order(symbol=sym, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                print("🛑 Cierre por cambio de señal")

        except Exception as e:
            print(f"⚠️ Alerta en ciclo: {e}")
        
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    ejecutar_sistema()
