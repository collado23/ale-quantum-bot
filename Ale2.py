import os, time
from binance.client import Client

# CONEXIÓN DIRECTA SIN TEXTO
def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['ETHUSDT', 'BNBUSDT', 'BTCUSDT']
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

def ni(k1, k2):
    o, h, l, c = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c - o) if abs(c - o) > 0 else 0.001
    mi, ms_ = min(o, c) - l, h - max(o, c)
    op_p, cl_p = float(k2[1]), float(k2[4])
    cp_p = abs(cl_p - op_p)
    if mi > (cp * 2.5) and ms_ < (cp * 0.7): return "🔨"
    if ms_ > (cp * 2.5) and mi < (cp * 0.7): return "☄️"
    if c > o and cl_p < op_p and cp > (cp_p * 1.1): return "V"
    if c < o and cl_p > op_p and cp > (cp_p * 1.1): return "R"
    return "."

print("📡 SISTEMA ON")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=3)
            p = ni(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['e']:
                print(f"{m[:2]}:{p}", end=' ')
                if (("🔨" in p or "V" in p) and px > cr) or (("☄️" in p or "R" in p) and px < cr):
                    s['t'] = "LONG" if "V" in p or "🔨" in p else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🔥 IN {m}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi
                if roi >= 0.18: s['b'] = True
                
                if (s['b'] and roi <= 0.01) or (s['m'] >= 0.40 and roi <= (s['m'] - 0.12)) or roi <= -0.55:
                    s['n'] += (30.76 * (roi / 100))
                    s['o'] += 1
                    s['e'] = False
                    print(f"\n✅ {m} {roi:.2f}% | NETO: {s['n']:.2f}")

        time.sleep(15)
    except Exception:
        time.sleep(10)
        cl = c()
