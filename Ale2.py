import os, time
from datetime import datetime
from binance.client import Client

# CONEXIÓN ULTRA-RÁPIDA
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()
# CAMBIO: Sacamos SOL, entra BNB
monedas = ['ETHUSDT', 'BNBUSDT', 'BTCUSDT']
stats = {m: {'neto': 0.0, 'ops': 0, 'en': False, 'p': 0, 't': '', 'mx': -99.0, 'be': False} for m in monedas}

def nison(k1, k2):
    o, h, l, c = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c - o) if abs(c - o) > 0 else 0.001
    mi, ms = min(o, c) - l, h - max(o, c)
    op_p, cl_p = float(k2[1]), float(k2[4])
    cp_p = abs(cl_p - op_p)
    # PATRONES NISON AGRESIVOS
    if mi > (cp * 2.5) and ms < (cp * 0.7): return "🔨" # Martillo
    if ms > (cp * 2.5) and mi < (cp * 0.7): return "☄️" # Estrella
    if c > o and cl_p < op_p and cp > (cp_p * 1.1): return "🌊V" # Env. Verde
    if c < o and cl_p > op_p and cp > (cp_p * 1.1): return "🌊R" # Env. Roja
    return "."

print("🔱 SNIPER: ETH | BNB | BTC 🔱")

while True:
    try:
        for m in monedas:
            s = stats[m]
            px = float(client.get_symbol_ticker(symbol=m)['price'])
            k = client.get_klines(symbol=m, interval='1m', limit=3)
            ptr = nison(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['en']:
                print(f"{m[:3]}:{ptr}", end=' ')
                if (("🔨" in ptr or "🌊V" in ptr) and px > cr) or \
                   (("☄️" in ptr or "🌊R" in ptr) and px < cr):
                    s['t'] = "LONG" if "V" in ptr or "🔨" in ptr else "SHORT"
                    s['p'], s['en'], s['mx'], s['be'] = px, True, -99.0, False
                    print(f"\n🔥 ENTRADA {m}: {s['t']}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22
                if roi > s['mx']: s['mx'] = roi
                if roi >= 0.18: s['be'] = True # BREAK BAD ACTIVADO
                
                # CIERRES
                if (s['be'] and roi <= 0.01) or (s['mx'] >= 0.40 and roi <= (s['mx'] - 0.12)) or roi <= -0.55:
                    res = (30.76 * (roi / 100))
                    s['neto'] += res
                    s['ops'] += 1
                    s['en'] = False
                    print(f"\n✅ {m} {s['t']} {roi:.2f}% | NETO: ${s['neto']:.4f}")
                    if s['ops'] % 5 == 0: print(f"📊 {m} BLOQUE 5 OK")

        time.sleep(15)
    except Exception as e:
        time.sleep(10)
        client = conectar()
