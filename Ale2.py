import os, time, sys
from binance.client import Client

def prueba_de_fuego():
    # Recupera las llaves de la pestaña Variables de Railway
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')

    print("🛡️ INICIANDO PRUEBA DE CONEXIÓN...")
    print(f"🌍 Región detectada: {os.getenv('RAILWAY_REGION', 'Alemania/Europa')}")

    try:
        # 1. Intento de Conexión
        client = Client(api_key, api_secret)
        
        # 2. Pedir Saldo (Prueba de llaves)
        balance = client.futures_account_balance()
        usdt_balance = next(b['balance'] for b in balance if b['asset'] == 'USDT')
        print(f"✅ CONEXIÓN EXITOSA!")
        print(f"💰 Tu saldo actual en Binance Futures es: {usdt_balance} USDT")

        # 3. Pedir Precio de ETH (Prueba de mercado)
        ticker = client.futures_symbol_ticker(symbol='ETHUSDT')
        print(f"📈 Precio actual de ETH: {ticker['price']}")
        
        print("\n🔥 CONCLUSIÓN: Todo está perfecto. Podemos cargar el bot completo.")

    except Exception as e:
        print("\n❌ FALLÓ LA PRUEBA")
        print(f"Motivo del error: {e}")
        if "restricted location" in str(e).lower():
            print("⚠️ BLOQUEO GEOGRÁFICO: Railway todavía está en EE.UU. Cambialo a Europa.")
        elif "API-key format" in str(e).lower():
            print("⚠️ ERROR DE LLAVES: Las API Keys están mal pegadas o tienen espacios.")

if __name__ == "__main__":
    prueba_de_fuego()
    # Mantiene el log abierto para que puedas leerlo
    time.sleep(60)
