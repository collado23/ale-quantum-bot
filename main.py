import requests, time, hmac, hashlib, os

# --- CONEXIÓN DE SEGURIDAD (Configurar en Variables de Railway) ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"

# --- TUS REGLAS DE ORO ---
SYMBOL = "ETHUSDT"
LEVERAGE = 10
MARGEN_USO = 0.20        # Interés compuesto: usamos el 20% del saldo
TRAILING_CALLBACK = 0.5  # El Stop que sube solo 0.5% (En la WEB)
UMBRAL_HACHAZO = 76      # Solo entra si las compras superan el 76%

def firmar(query):
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def obtener_datos_cuenta():
    ts = int(time.time() * 1000)
    query = f"timestamp={ts}"
    firma = firmar(query)
    res = requests.get(f"{BASE_URL}/fapi/v2/balance?{query}&signature={firma}", 
                        headers={"X-MBX-APIKEY": API_KEY}).json()
    for moneda in res:
        if moneda['asset'] == 'USDT':
            return float(moneda['balance'])
    return 0.0

def ejecutar_estrategia_web(lado, cantidad):
    """Manda la entrada y el Trailing Stop a la WEB de Binance"""
    ts = int(time.time() * 1000)
    
    # 1. EL HACHAZO (Entrada a mercado)
    q_entrar = f"symbol={SYMBOL}&side={lado}&type=MARKET&quantity={cantidad}&timestamp={ts}"
    f_entrar = firmar(q_entrar)
    requests.post(f"{BASE_URL}/fapi/v1/order?{q_entrar}&signature={f_entrar}", headers={"X-MBX-APIKEY": API_KEY})
    
    # 2. EL TRAILING STOP (Cargado en la WEB para que no se tilde)
    lado_cierre = "SELL" if lado == "BUY" else "BUY"
    time.sleep(1.5) # Pausa para que Binance registre la posición
    
    q_trailing = (f"symbol={SYMBOL}&side={lado_cierre}&type=TRAILING_STOP_MARKET"
                  f"&quantity={cantidad}&callbackRate={TRAILING_CALLBACK}&timestamp={ts+2000}")
    f_trailing = firmar(q_trailing)
    res_trailing = requests.post(f"{BASE_URL}/fapi/v1/order?{q_trailing}&signature={f_trailing}", 
                                  headers={"X-MBX-APIKEY": API_KEY})
    print(f"✅ Hachazo dado y Trailing Stop cargado en la WEB: {res_trailing.json()}")

def radar_200_niveles():
    print(f"🚀 ALE IA QUANTUM ACTIVADO | Saldo objetivo inicial: $36.62")
    # Ajustamos apalancamiento al iniciar
    ts = int(time.time() * 1000)
    q_lev = f"symbol={SYMBOL}&leverage={LEVERAGE}&timestamp={ts}"
    requests.post(f"{BASE_URL}/fapi/v1/leverage?{q_lev}&signature={firmar(q_lev)}", headers={"X-MBX-APIKEY": API_KEY})

    while True:
        try:
            # ANALISIS DE LIBRO DE 200 NIVELES (Separamos C y V)
            res = requests.get(f"{BASE_URL}/fapi/v1/depth?symbol={SYMBOL}&limit=500").json()
            c_200 = sum(float(b[1]) for b in res['bids'][:200]) # Compras
            v_200 = sum(float(a[1]) for a in res['asks'][:200]) # Ventas
            p_suba = (c_200 / (c_200 + v_200)) * 100

            print(f"⏱️ {time.strftime('%H:%M:%S')} | Radar: {p_suba:.1f}% | C: {c_200:.1f} | V: {v_200:.1f}")

            # SEÑAL DE ENTRADA
            if p_suba > UMBRAL_HACHAZO:
                saldo = obtener_datos_cuenta()
                precio_eth = float(res['bids'][0][0])
                # Cálculo de cantidad con interés compuesto del 20% y x10
                cantidad = round((saldo * MARGEN_USO * LEVERAGE) / precio_eth, 3)
                
                print(f"🔥 SEÑAL DETECTADA ({p_suba:.1f}%). Usando {cantidad} ETH...")
                ejecutar_estrategia_web("BUY", cantidad)
                time.sleep(600) # Esperamos 10 min para no repetir en la misma subida

            time.sleep(15) # Escaneo cada 15 segundos

        except Exception as e:
            print(f"⚠️ Error en Radar: {e}")
            time.sleep(10)

if __name__ == "__main__":
    radar_200_niveles()
