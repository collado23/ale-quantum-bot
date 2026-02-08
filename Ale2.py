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
            dec, p, adx, vol = IA_Estratega.analizar_mercado(client, sym)
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            print(f"🔎 ETH:{p} | ADX:{round(adx,1)} | Señal:{dec} | Pos:{amt}")

            if amt == 0 and dec in ["LONG", "SHORT"]:
                try:
                    cap = next(float(b['balance']) for b in client.futures_account_balance() if b['asset'] == 'USDT')
                    qty = round(((cap * 0.20) * 10) / p, 3)
                    
                    # Entrada y Trailing 0.9%
                    client.futures_create_order(symbol=sym, side='BUY' if dec=="LONG" else 'SELL', type='MARKET', quantity=qty)
                    client.futures_create_order(symbol=sym, side='SELL' if dec=="LONG" else 'BUY', type='TRAILING_STOP_MARKET', callbackRate=0.9, quantity=qty, reduceOnly=True)
                
                except Exception as error_binance:
                    # GUARDAR EL ERROR PARA NO REPETIRLO
                    with open("error_log.txt", "w") as f:
                        f.write(f"Precio:{p} | Error:{error_binance}")
                    print(f"❌ Error guardado en memoria: {error_binance}")

        except Exception as e: print(f"⚠️ Error: {e}")
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__": ejecutar_sistema()
