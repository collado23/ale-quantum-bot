import time

# --- CONFIGURACIÓN DE IDENTIDAD Y SEGURIDAD ---
NOMBRE_BOT = "GATITO QUANTUM v6 GOLD - SISTEMA CHAJÁ"
VERSION = "2.0 Dual-Core"

# --- PARÁMETROS DE ESTRATEGIA (Guardados en Memoria) ---
CAPITAL_INICIAL = 36.02
APALANCAMIENTO = 10           # x10 como siempre, Ale
PORCENTAJE_OPERACION = 0.20   # 20% de interés compuesto
DISTANCIA_MIN_EMA = 5.0       # Tu filtro de seguridad
COMISION_BINANCE = 0.001      # 0.1% de comisión

# Umbrales de ADX
ADX_HACHAZO = 24.0            # El nivel de máxima confianza
ADX_CAZADORA = 19.0           # El nivel de acción rápida que pediste

def analizar_mercado(adx_actual, distancia_ema, precio_actual):
    """
    Cerebro del Bot: Decide si entra por Hachazo, por Cazadora o si espera.
    """
    print(f"--- Monitoreando ETH: ADX {adx_actual} | Distancia {distancia_ema} ---")
    
    # Verificamos primero la Distancia EMA (Filtro Maestro)
    if distancia_ema < DISTANCIA_MIN_EMA:
        return "ESPERAR", "Distancia insuficiente para evitar Zig-Zag."

    # PRIORIDAD 1: EL HACHAZO SEGURO (ADX 24+)
    if adx_actual >= ADX_HACHAZO:
        return "EJECUTAR_HACHAZO", f"🔱 SEÑAL DE PODER: ADX {adx_actual} detectado."

    # PRIORIDAD 2: LA CAZADORA (ADX 19 a 23.9)
    elif adx_actual >= ADX_CAZADORA:
        return "EJECUTAR_CAZADORA", f"🎯 SEÑAL RÁPIDA: ADX {adx_actual} detectado."

    else:
        return "ESPERAR", "Mercado sin fuerza (ADX bajo)."

def calcular_posicion(saldo_actual):
    """
    Maneja el interés compuesto del 20% sobre el saldo real.
    """
    margen = saldo_actual * PORCENTAJE_OPERACION
    posicion_total = margen * APALANCAMIENTO
    return margen, posicion_total

# --- BUCLE PRINCIPAL (Simulación de Log en Railway) ---
def ejecutar_bot():
    saldo_en_cuenta = CAPITAL_INICIAL
    operacion_activa = False
    
    print(f"🚀 {NOMBRE_BOT} INICIADO")
    print(f"💰 Capital: ${saldo_en_cuenta} | Estrategia: Dual (19/24)")
    print("---------------------------------------------------------")

    while True:
        # Aquí el bot leería los datos reales de Binance
        # Simulamos valores para el ejemplo de los logs:
        adx_real = 19.5       # Ejemplo: Está en nivel "Cazadora"
        distancia_real = 5.2  # Ejemplo: Cumple el filtro de 5
        precio_eth = 2500.0
        
        decision, motivo = analizar_mercado(adx_real, distancia_real, precio_eth)
        
        if not operacion_activa:
            if decision == "EJECUTAR_HACHAZO" or decision == "EJECUTAR_CAZADORA":
                margen, total = calcular_posicion(saldo_en_cuenta)
                print(f"✅ {motivo}")
                print(f"🔥 ABRIENDO OPERACIÓN: Margen ${margen:.2f} | Total x10: ${total:.2f}")
                operacion_activa = True
                # Aquí iría la orden real a Binance API
        
        # Pausa para no saturar el servidor de Railway
        time.sleep(60) 

if __name__ == "__main__":
    ejecutar_bot()
