import yfinance as yf
import pandas as pd
import numpy as np
import time

def generar_espejo_eth():
    print("📡 Conectando con la base de datos de Yahoo Finance para ETH...")
    
    # 1. Descargamos 5 años para tener un margen sólido de 4 años limpios
    data = yf.download("ETH-USD", period="5y", interval="1d", progress=False)
    
    # Limpieza de columnas por si vienen en formato MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    df = data.copy()
    
    # 2. Cálculo de la Distancia Cuántica (EMA 200)
    # Usamos 200 días para la historia larga, que es la que marca la tendencia de capital
    df['ema'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['elast'] = ((df['Close'] - df['ema']) / df['ema']) * 100
    
    # 3. Filtramos los "Latigazos" (Picos donde el elástico se estiró más de 1.8%)
    # Para ETH, un 1.8% en diario es una señal de gran movimiento
    picos = df[abs(df['elast']) > 1.8].copy()
    
    print(f"🧠 Analizando ciclos... Se detectaron {len(picos)} patrones de alta ganancia.")
    
    # 4. Guardamos en el archivo TXT para que el bot lo use de espejo
    nombre_archivo = "espejo_cuantico_eth.txt"
    try:
        with open(nombre_archivo, "w") as f:
            # Escribimos una cabecera para que sepas qué es cada cosa
            f.write("# Fecha_Unix,Elasticidad,ROI_Historico_Estimado\n")
            for index, row in picos.iterrows():
                # Convertimos la fecha a timestamp (formato que entiende el bot)
                unix_time = int(time.mktime(index.timetuple()))
                # Estimamos un ROI de regreso según la elasticidad (física pura)
                roi_estimado = abs(row['elast']) * 0.9 
                f.write(f"{unix_time},{row['elast']:.2f},{roi_estimado:.2f}\n")
        
        print(f"✅ ¡Éxito! El archivo '{nombre_archivo}' ha sido creado con 4 años de ADN.")
        print("🚀 Ahora Ethereum ya tiene memoria para no repetir errores.")
        
    except Exception as e:
        print(f"⚠️ Error al crear el espejo: {e}")

if __name__ == "__main__":
    generar_espejo_eth()
