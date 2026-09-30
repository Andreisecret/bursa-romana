"""check.py — singurul check rulabil: ancorele din presa trebuie reproduse.
Asertii pe randamente BRUTE (nu anormale), tolerante largi pt open-vs-close.
Rulare: python check.py (exit 0 = totul reproduce, !=0 = pipeline rupt)
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
px = pd.read_csv(ROOT / "data" / "prices_daily.csv", parse_dates=["date"]).pivot(
    index="date", columns="ticker", values="close").sort_index()

def raw(ticker, day):
    day = pd.Timestamp(day)
    prev = px.index[px.index.get_loc(day) - 1]
    return (px.loc[day, ticker] / px.loc[prev, ticker] - 1) * 100

fails = []
def check(nume, val, lo, hi):
    ok = lo <= val <= hi
    print(f"{'OK ' if ok else 'FAIL'} {nume}: {val:+.2f}% (asteptat [{lo:+.2f},{hi:+.2f}])")
    if not ok:
        fails.append(nume)

# 1. Bursa.ro 26.11.2024: "recul de 0,89%, la 16.982 puncte" (ziua de 25 nov)
check("BET 2024-11-25 tur1 Georgescu", raw("BET", "2024-11-25"), -1.2, -0.6)
assert abs(px.loc["2024-11-25", "BET"] - 16982) < 5, "nivel BET 16982"
print("OK  nivel BET 25.11.2024 = 16982 (Bursa.ro)")
# 2. Profit.ro 05.05.2025 intraday -1.69% la 14:00; inchiderea a fost mai jos
v = raw("BET", "2025-05-05")
check("BET 2025-05-05 tur1 Simion (inchidere < intraday -1.69%)", v, -3.5, -1.7)
# 3. Profit.ro 06.05.2025: "a mai pierdut jumatate de procent"
check("BET 2025-05-06 (-0.5%)", raw("BET", "2025-05-06"), -0.9, -0.1)
# 4. Bancile lovite cel mai tare pe 5 mai (TLV ~-4%)
check("TLV 2025-05-05 soc bancar", raw("TLV", "2025-05-05"), -5.0, -2.5)
# 5. outputs generate
for f in ["outputs/event_table.csv", "outputs/group_test.csv",
          "outputs/fig_bet_timeline.png", "outputs/fig_car_paths.png",
          "outputs/fig_bet_vs_stoxx.png", "outputs/fig_indices_car3.png",
          "data/intraday_15m.csv", "data/bench_daily.csv"]:
    ok = (ROOT / f).exists()
    print(f"{'OK ' if ok else 'FAIL'} exista {f}")
    if not ok:
        fails.append(f)
# 6. control extern: 25.11.2024 Europa verde/plat, BVB rosu => soc intern
import numpy as np
bx = pd.read_csv(ROOT / "data" / "bench_daily.csv", parse_dates=["date"]).set_index("date").sort_index()
sx = bx["stoxx_close"].reindex(px.index).ffill().pct_change() * 100
div = float((px["BET"].pct_change() * 100).loc["2024-11-25"] - sx.loc["2024-11-25"])
ok = sx.loc["2024-11-25"] > -0.3 and div < -0.5
print(f"{'OK ' if ok else 'FAIL'} divergenta RO vs EU 25.11.2024: STOXX {sx.loc['2024-11-25']:+.2f}%, BET-STOXX {div:+.2f}pp")
if not ok:
    fails.append("divergenta")
# 7. ROTX confirma BET la socul din mai-2025 (acelasi cos, aceeasi directie)
rr = float((px["ROTX"].pct_change() * 100).loc["2025-05-05"])
ok = rr < -1.5
print(f"{'OK ' if ok else 'FAIL'} ROTX 2025-05-05: {rr:+.2f}% (confirma BET)")
if not ok:
    fails.append("rotx")
# 8. testul de grup extins (2020-2026) e calculat; trio-ul electoral 2024-2025
# ramane semnificativ (eterogenitatea clasei largi e rezultat, nu eroare)
import numpy as np
g = pd.read_csv(ROOT / "outputs" / "group_test.csv")
t = pd.read_csv(ROOT / "outputs" / "event_table.csv")
text = t[t.event_id.isin(["tur1_2024", "parlamentare_2024", "tur1_2025"])]["bet_car3"].values
tnarrow = text.mean() / (text.std(ddof=1) / np.sqrt(len(text)))
nrow = int(g[g.grup == "negativ"]["n"].iloc[0])
ok = nrow == 7 and tnarrow < -2
print(f"{'OK ' if ok else 'FAIL'} grup extins n={nrow}, trio electoral 2024-2025 t={tnarrow:.2f} (<-2)")
if not ok:
    fails.append("grup")
# 9. socurile globale 2020/2022 sunt in tabel cu AR0 semnificativ (sanity extern)
for eid, lo in [("covid_urgenta_2020", -12.0), ("invazie_2022", -6.0)]:
    v = float(t[t.event_id == eid]["bet_ar0"].iloc[0])
    ok = v < -2 and v > lo
    print(f"{'OK ' if ok else 'FAIL'} {eid} AR0={v:+.2f}% (soc global vizibil)")
    if not ok:
        fails.append(eid)
raise SystemExit(1 if fails else print("TOATE CHECK-URILE TREC"))
