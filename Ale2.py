import yfinance as yf
import pandas as pd
import os
import sys

def inyeccion_adn_eth():
    nombre_archivo = "espejo_cuantico_eth.txt"
    
    print("🧹 PASO 1: Limpiando archivos viejos...")
    # Borramos CUALQUIER archivo que pueda estar causando conflicto
    archivos_a_borrar = [nombre_archivo, "espejo_cuantico.txt"]
    for arc in archivos_a_borrar:
        if os.path.exists(arc):
            try:
                os.remove(arc)
                print(f"🗑️ Eliminado con éxito: {arc}")
            except:
                print(f"⚠️ No se pudo borrar {arc}, intentando sobreescribir...")

    print("\n📡 PASO 2: Descargando 4 años de historia pura de ETH...")
    try:
        # Descargamos ETH-USD (5 años para asegurar 200 días de EMA inicial)
        df = yf.download("ETH-USD", period="5y", interval="1d", progress=False)
        
        if df.empty:
            print("❌ ERROR: No se pudieron descargar datos de Yahoo. Revisá tu conexión.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Cálculo de la Física Cuántica (EMA 200)
        df['ema'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['dist'] = ((df['Close'] - df['ema']) / df['ema']) * 100
        
        # Filtramos los momentos de tensión (>1.8%)
        adn = df[abs(df['dist']) > 1.8].copy()

        print(f"\n🧠 PASO 3: Grabando {len(adn)} patrones en el nuevo Espejo...")
        
        # Abrimos con 'w+' para asegurar que se cree de cero y se pueda escribir
        with open(nombre_archivo, "w+") as f:
            f.write("# ADN_ETHEREUM_4_AÑOS_LIMPIO\n")
            for fecha, fila in adn.iterrows():
                f.write(f"{int(fecha.timestamp())},{fila['dist']:.2f},{fila['Close']:.2f}\n")
            # Forzamos al sistema a guardar en disco
            f.flush()
            os.fsync(f.fileno())

        print(f"\n✅ ¡PROCESO COMPLETADO!")
        print(f"📂 El archivo '{nombre_archivo}' ahora es 100% ETHEREUM.")
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    inyeccion_adn_eth()
