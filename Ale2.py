import time, os, sys, IA_Estratega
from binance.client import Client

def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        # Conexión usando las llaves de Railway
        client = Client(os.getenv('API_KEY'), os.getenv('API_SECRET'))
        print("⚔️ Gladiador ETH: Conexión Exitosa")
    except Exception as e:
        print(f"❌ Error API: {e}")
        return

    while True:
        try:
            # Pedimos los 4 datos al Cerebro
            datos = IA_Estratega.analizar_mercado(client, sym)
            dec, p, adx, vol = datos[0], datos[1], datos[2], datos[3]
            
            # Revisamos si tenemos posición abierta
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            # Mostramos info en la consola de Railway
            print(f"🔎 ETH:{p} | ADX:{round(adx,1)} | Señal:{dec} | Pos:{amt}")

            # ENTRADA: Solo si no hay posición y el ADX es mayor a 25
            if amt == 0 and dec in ["LONG", "SHORT"]:
                # Interés compuesto 20% de la cuenta x10 de leverage
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # ESCUDO DISTANCIA 9 (Trailing Stop 0.9%)
                inv_side = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=sym, 
                    side=inv_side, 
                    type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, 
                    quantity=qty, 
                    reduceOnly=True
                )
                print(f"🚀 {dec} abierto con Distancia 9")

        except Exception as e:
            print(f"⚠️ Reintentando... {e}")
            
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    ejecutar_sistema()
