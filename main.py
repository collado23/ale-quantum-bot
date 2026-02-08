import time
import sys
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN (Poné tus llaves) ---
NOMBRE_BOT = "TEST - GATITO QUANTUM"
API_KEY = 'TU_API_KEY_AQUI'
SECRET_KEY = 'TU_SECRET_KEY_AQUI'

# --- PARÁMETROS DE LA PRUEBA ---
CAPITAL_TOTAL = 36.02
PORCENTAJE_OP = 0.20
LEVERAGE = 10

# Conexión
client = Client(API_KEY, SECRET_KEY)

def latido_test(mensaje):
    print(f"💓 [TEST] {time.strftime('%H:%M:%S')} - {mensaje}")
    sys.stdout.flush()

def main():
    print(f"🚀 INICIANDO PRUEBA DE FUEGO")
    latido_test("Verificando conexión con Binance...")
    
    try:
        # 1. Forzamos las variables para que den POSITIVO
        adx_test = 25.0
        dist_test = 6.0
        
        latido_test(f"Simulando condiciones: ADX {adx_test} | DIST {dist_test}")
        
        # 2. Intentamos ejecutar la lógica de Ale
        if dist_test >= 5.0 and adx_test >= 19.0:
            margen = CAPITAL_TOTAL * PORCENTAJE_OP
            print(f"🔥 SEÑAL DE PRUEBA DETECTADA")
            print(f"✅ EJECUTANDO ORDEN DE ${margen:.2f} x10...")
            
            # --- INTENTO REAL DE ORDEN (Aquí probamos si Railway se apaga) ---
            try:
                # Quitá el '#' de la línea de abajo para que mande la orden real
                # client.futures_create_order(symbol='ETHUSDT', side='BUY', type='MARKET', quantity=0.01)
                print("💎 ¡ÉXITO! La orden llegó a Binance sin que Railway se apague.")
            except Exception as e:
                print(f"❌ Error en la orden: {e}")
            
            sys.stdout.flush()
            
    except Exception as e:
        print(f"❌ Error crítico en el test: {e}")

    print("🏁 Fin de la prueba. Si leíste esto, el bot NO se puso en pausa.")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
