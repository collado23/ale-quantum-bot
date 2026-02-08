import time, os, sys, IA_Estratega
from binance.client import Client

def ejecutar_sistema():
    sym = 'ETHUSDT'
    try:
        # Cargamos las llaves de las variables de entorno de Railway
        api = os.getenv('API_KEY')
        sec = os.getenv('API_SECRET')
        client = Client(api, sec)
        print("⚔️ Gladiador ETH: Conexión Exitosa")
    except Exception as e:
        print(f"❌ Error de Conexión: {e}")
        return

    while True:
        try:
            # 1. ANALIZAMOS: Recibimos los 4 valores (incluyendo la línea de volumen)
            dec, p, adx, vol_diff = IA_Estratega.analizar_mercado(client, sym)
            
            # Verificamos si hay posición abierta
            pos = client.futures_position_information(symbol=sym)
            amt = next(float(i['positionAmt']) for i in pos if i['symbol'] == sym)
            
            # Logs para control total en Railway
            print(f"🔎 ETH: {p} | ADX: {round(adx,1)} | Vol: {round(vol_diff,1)} | Señal: {dec} | Pos: {amt}")

            # 2. LÓGICA DE ENTRADA (Si no hay posición y el ADX > 25)
            if amt == 0 and dec in ["LONG", "SHORT"]:
                bal = client.futures_account_balance()
                cap = next(float(b['balance']) for b in bal if b['asset'] == 'USDT')
                
                # Interés compuesto al 20% con apalancamiento x10
                qty = round(((cap * 0.20) * 10) / p, 3)
                
                side = 'BUY' if dec == "LONG" else 'SELL'
                client.futures_create_order(symbol=sym, side=side, type='MARKET', quantity=qty)
                
                # 3. TRAILING STOP WEB (DISTANCIA 9 = 0.9%)
                # Esto es lo que permite que el precio corra sin que el zigzag te saque
                inv_side = 'SELL' if side == 'BUY' else 'BUY'
                client.futures_create_order(
                    symbol=sym, 
                    side=inv_side, 
                    type='TRAILING_STOP_MARKET', 
                    callbackRate=0.9, # TU DISTANCIA DE 9
                    quantity=qty, 
                    reduceOnly=True
                )
                print(f"🚀 {side} ejecutado con Escudo de 0.9% (Distancia 9)")

            # 4. CIERRE POR CAMBIO DE SEÑAL TÉCNICA
            elif amt != 0 and ((amt > 0 and dec == "SHORT") or (amt < 0 and dec == "LONG")):
                client.futures_cancel_all_open_orders(symbol=sym)
                client.futures_create_order(
                    symbol=sym, 
                    side='SELL' if amt > 0 else 'BUY', 
                    type='MARKET', 
                    quantity=abs(amt)
                )
                print("🛑 Cierre total por cambio de tendencia")

        except Exception as e:
            print(f"⚠️ Alerta en ciclo: {e}")
        
        # Obligamos a Railway a mostrar los logs inmediatamente
        sys.stdout.flush()
        time.sleep(30)

if __name__ == "__main__":
    ejecutar_sistema()
