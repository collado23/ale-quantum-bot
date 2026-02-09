import yfinance as yf
import pandas as pd
import os

def descargar_adn_eth_5m():
    archivo = "espejo_eth.txt"
    simbolo = "ETH-USD"

    print(f"📡 Descargando micro-ciclos de 5 minutos para {simbolo}...")
    
    # Bajamos los últimos 60 días (el máximo permitido para 5m)
    # Esto genera miles de filas de datos, suficiente para el ADN
    df = yf.download(simbolo, period="60d", interval="5m", progress=False)
    
    if df.empty:
        print("❌ Error: No se pudo descargar la data. Revisá internet.")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    print("🧠 Calculando EMA 200 y Elasticidad Cuántica...")
    # Calculamos la EMA 200 sobre velas de 5 minutos
    df['ema200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['distancia'] = ((df['Close'] - df['ema200']) / df['ema200']) * 100

    # Filtramos los latigazos de ETH (En 5m, un 1.5% o 1.8% ya es señal de rebote)
    adn_puro = df[abs(df['distancia']) > 1.5].copy()

    try:
        with open(archivo, "w") as f:
            f.write("# ADN_ETH_5M_ULTIMOS_60_DIAS\n")
            for fecha, fila in adn_puro.iterrows():
                # Guardamos: Timestamp, Distancia, Precio
                f.write(f"{int(fecha.timestamp())},{fila['distancia']:.2f},{fila['Close']:.2f}\n")
        
        print(f"✅ ¡ADN 5M CARGADO! Se encontraron {len(adn_puro)} puntos de alta tensión.")
        print(f"📂 Archivo generado: {archivo}")
        print("💡 Ahora subí este archivo a tu GitHub para que Ale2.py lo use.")
        
    except Exception as e:
        print(f"⚠️ Error al guardar: {e}")

if __name__ == "__main__":
    descargar_adn_eth_5m()
