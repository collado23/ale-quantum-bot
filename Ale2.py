import yfinance as yf
import pandas as pd
import os

def resetear_y_cargar_adn_eth():
    archivo = "espejo_cuantico_eth.txt"
    
    # 1. Forzamos el borrado del archivo viejo si existe para que no se pegue
    if os.path.exists(archivo):
        os.remove(archivo)
        print(f"🗑️ Archivo viejo eliminado: {archivo}")

    print("📡 Descargando ADN fresco de Ethereum (Últimos 4 años)...")
    
    # 2. Descargamos la data de ETH-USD
    # Usamos un periodo de 5 años para asegurar 4 años de EMA 200 bien calculada
    df = yf.download("ETH-USD", period="5y", interval="1d", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 3. Calculamos la EMA 200 y la Distancia (La física del espejo)
    df['ema200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['distancia'] = ((df['Close'] - df['ema200']) / df['ema200']) * 100

    # 4. Filtramos solo los momentos donde el elástico se estiró de verdad (>1.8%)
    # Esto es lo que el bot usará para comparar en el futuro
    adn_puro = df[abs(df['distancia']) > 1.8].copy()

    # 5. Guardamos el nuevo archivo limpio
    try:
        with open(archivo, "w") as f:
            f.write("# ADN_ETH_4_AÑOS\n")
            for fecha, fila in adn_puro.iterrows():
                # Guardamos: Fecha (Unix), Distancia, Precio
                f.write(f"{int(fecha.timestamp())},{fila['distancia']:.2f},{fila['Close']:.2f}\n")
        
        print(f"✅ ¡ADN Ethereum cargado con éxito! {len(adn_puro)} patrones detectados.")
        print(f"📂 Archivo listo: {archivo}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    resetear_y_cargar_adn_eth()
