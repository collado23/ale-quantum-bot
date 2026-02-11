import os, time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ÚNICA ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === CONFIGURACIÓN DUAL ===
monedas = ['SOLUSDT', 'ETHUSDT']
cap_base = 30.76
stats = {m: {'ganado': 0.0, 'perdido': 0.0, 'ops': 0, 'hist': [], 'en_op': False, 'p_ent': 0, 't_op': '', 'patron': '', 'max_roi': -99.0, 'be': False} for m in monedas}

def libro_nison(k1, k2):
    op, hi, lo, cl = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cuerpo = abs(cl - op) if abs(cl - op) > 0 else 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    op_p, cl_p = float(k2[1]), float(k2[4])
    cuerpo_p = abs(cl_p - op_p)
    # Patrones
    if m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.7): return "MARTILLO 🔨"
    if cl > op and cl_p < op_p and cuerpo > (cuerpo_p * 1.1): return "ENVOLVENTE_V 🌊"
    if m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.7): return "ESTRELLA ☄️"
    if cl < op and cl_p > op_p and cuerpo > (cuerpo_p * 1.1): return "ENVOLVENTE_R 🌊"
    return "Normal"

print("🚀 INICIANDO MODO DUAL (SOL + ETH) - ANTI-COLA ACTIVADO")

while True:
    try:
        for m in monedas:
            s = stats[m]
            ticker = client.get_symbol_ticker(symbol=m)
            precio = float(ticker['price'])
            k = client.get_klines(symbol=m, interval='1m', limit=3)
            patron = libro_nison(k[-1], k[-2])
            cierre_v1 = float(k[-1][4])

            if not s['en_op']:
                print(f"📡 SCAN {m[:3]}: {patron} | ${precio:.2f}", end=' | ')
                # Gatillos
                if (("MARTILLO" in patron or "ENVOLVENTE_V" in patron) and precio > cierre_v1) or \
                   (("ESTRELLA" in patron or "ENVOLVENTE_R" in patron) and precio < cierre_v1):
                    s['t_op'] = "LONG" if "V" in patron or "MARTILLO" in patron else "SHORT"
                    s['p_ent'], s['en_op'], s['patron'] = precio, True, patron
                    s['max_roi'], s['be'] = -99.0, False
                    print(f"\n🔥 ENTRADA {m}: {s['t_op']} por {patron}")
            else:
                diff = (precio - s['p_ent']) / s['p_ent'] if s['t_op'] == "LONG" else (s['p_ent'] - precio) / s['p_ent']
                roi = (diff * 100 * 10) - 0.22
                if roi > s['max_roi']: s['max_roi'] = roi
                if roi >= 0.18: s['be'] = True # Break Even
                
                # Cierres
                if (s['be'] and roi <= 0.01) or (s['max_roi'] >= 0.40 and roi <= (s['max_roi'] - 0.12)) or roi <= -0.55:
                    res = (cap_base * (roi / 100))
                    s['ops'] += 1
                    if res > 0: s['ganado'] += res; ico = "✅"
                    else: s['perdido'] += abs(res); ico = "❌"
                    s['hist'].append(f"{ico} {m[:3]} {s['t_op']} {roi:.2f}%")
                    s['en_op'] = False
                    
                    if s['ops'] % 5 == 0:
                        print(f"\n📊 REPORTE {m}: NETO ${s['ganado']-s['perdido']:.4f}")
                        s['hist'] = []

        print(f"| {datetime.now().strftime('%H:%M:%S')}", end='\r')
        time.sleep(15)

    except Exception as e:
        time.sleep(10)
        client = conectar()
