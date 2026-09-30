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
# 8. testul de grup: DEMOTAT la descriptiv (etichetele expected sunt ex-post, test circular)
g = pd.read_csv(ROOT / "outputs" / "group_test.csv")
t = pd.read_csv(ROOT / "outputs" / "event_table.csv")
ok = "t_cross_DESCRIPTIV" in g.columns and (g["nota"].str.contains("circular").all())
print(f"{'OK ' if ok else 'FAIL'} test de grup demotat la descriptiv (etichete ex-post)")
if not ok:
    fails.append("grup_demotare")
# 9. socurile globale 2020/2022 sunt in tabel cu AR0 semnificativ (sanity extern)
for eid, lo in [("covid_urgenta_2020", -12.0), ("invazie_2022", -6.0)]:
    v = float(t[t.event_id == eid]["bet_ar0"].iloc[0])
    ok = v < -2 and v > lo
    print(f"{'OK ' if ok else 'FAIL'} {eid} AR0={v:+.2f}% (soc global vizibil)")
    if not ok:
        fails.append(eid)

# 10. CONTAMINATIE DIVIDEND: ajust=1 nu ajusteaza dividendele -> doar evenimentul
# din iunie 2024 (sezon de dividende) trebuie flagat automat, si numai el.
cont = t[t.contaminat_dividend]
ok = set(cont.event_id) == {"locale_euro_2024"}
print(f"{'OK ' if ok else 'FAIL'} contaminatie dividend: {list(cont.event_id)} (asteptat: locale_euro_2024)")
if not ok:
    fails.append("contaminatie")
# efectiv: pe randamentul total evenimentul dispare
r = t[t.event_id == "locale_euro_2024"].iloc[0]
ok = abs(r["bet_car3"]) - abs(r["car3_tr"]) > 2.0
print(f"{'OK ' if ok else 'FAIL'} locale_euro_2024: BET {r['bet_car3']:+.2f}% -> BET-TR {r['car3_tr']:+.2f}% (dividend)")
if not ok:
    fails.append("tr_effect")

# 11. PLACEBO: calibrul arata ca un CAR3 de 3% este obisnuit la BVB; doar tur2_2025
# se separa de null. Asta e rezultatul onest al studiului si trebuie reflectat in paper.
p = pd.read_csv(ROOT / "outputs" / "placebo_results.csv")
null = pd.read_csv(ROOT / "outputs" / "placebo_null.csv")["pseudo_car3_tr_pct"]
p95 = float(np.percentile(np.abs(null), 95))
sig5 = sorted(p[p.p_empilateric < 0.05].event_id.tolist())
ok = p95 > 3.0 and sig5 == ["ccr_anulare_2024", "fitch_negativ_2024", "tur2_2025"]
print(f"{'OK ' if ok else 'FAIL'} placebo: |CAR3| p95 = {p95:.2f}% ; p<0.05 -> {sig5}")
if not ok:
    fails.append("placebo")
print(f"     (tur2_2025 p={p[p.event_id=='tur2_2025'].p_empilateric.iloc[0]:.3f}; "
      f"parlamentare_2024 p={p[p.event_id=='parlamentare_2024'].p_empilateric.iloc[0]:.3f} — NU semnificativ)")
for f in ["outputs/placebo_null.csv", "outputs/placebo_results.csv", "outputs/fig_placebo.png"]:
    if not (ROOT / f).exists():
        fails.append(f)

# 12. tabelele din paper sunt GENERATE din date -> nu se pot dezacordea
import re
for f in ["macros.tex", "tab_events.tex", "tab_main.tex", "tab_speed.tex",
          "tab_idx.tex", "tab_placebo.tex"]:
    ok = (ROOT / "paper" / "tables" / f).exists()
    print(f"{'OK ' if ok else 'FAIL'} generat paper/tables/{f}")
    if not ok:
        fails.append(f)
mac = (ROOT / "paper" / "tables" / "macros.tex").read_text(encoding="utf-8")
names = re.findall(r"\\newcommand\{\\([^}]+)\}", mac)
bad = [n for n in names if not n.isalpha()]   # TeX: cifrele taie control word-ul
ok = not bad
print(f"{'OK ' if ok else 'FAIL'} {len(names)} macro-uri, toate doar litere" +
      (f" (OFENDE: {bad})" if bad else ""))
if not ok:
    fails.append("macro_nume")
# cifrele-cheie din prosa trebuie sa existe ca macro, nu scrise manual
for need in ["NullSd", "NullPqfive", "TurTwoCar", "TurTwoP", "LocaleTr", "CiucaStoxx",
             "AggP", "EvMeanAbs", "NullMeanAbs", "RhoWindow", "PqPostCovid"]:
    ok = f"\\{need}" in mac
    print(f"{'OK ' if ok else 'FAIL'} macro prezent: \\{need}")
    if not ok:
        fails.append(need)
# ...si niciun \\Macro folosit in paper.tex sa nu fie nedefinit
tex = (ROOT / "paper" / "paper.tex").read_text(encoding="utf-8")
used = set(re.findall(r"\\([A-Z][A-Za-z]*)", tex))
known = set(names) | {"N", "LaTeX", "TeX", "URL"}
undef = sorted(used - known)
ok = not undef
print(f"{'OK ' if ok else 'FAIL'} {len(used)} macro-uri folosite in paper.tex, toate definite" +
      (f" (OFENDE: {undef})" if undef else ""))
if not ok:
    fails.append("macro_nefolosit")

# 13. testul agregat: efectele politice se departa de zgomot in ansamblu
s = pd.read_csv(ROOT / "outputs" / "placebo_summary.csv").iloc[0]
ok = s.p_agregat < 0.05 and s.ev_mean_abs > s.null_mean_abs
print(f"{'OK ' if ok else 'FAIL'} test agregat: |CAR| mediu evenimente {s.ev_mean_abs:.2f}% "
      f"vs {s.null_mean_abs:.2f}% zile oarecare, p = {s.p_agregat:.3f} (<0.05)")
if not ok:
    fails.append("agregat")
# 14. sensibilitate: rangul evenimentelor nu depinde de fereastra de estimare
ok = s.rho_fereastra_min > 0.9
print(f"{'OK ' if ok else 'FAIL'} sensibilitate la fereastra: rho minim = "
      f"{s.rho_fereastra_min:.3f} (>0.9)")
if not ok:
    fails.append("sensibilitate")
# 15. null-ul post-COVID confirma ca cozile nu sunt artefact de pandemie
ok = abs(s.null_p95_postcovid - s.null_p95) < 0.3
print(f"{'OK ' if ok else 'FAIL'} p95 post-COVID {s.null_p95_postcovid:.2f}% vs "
      f"intreg {s.null_p95:.2f}% (diferenta <0.3pp)")
if not ok:
    fails.append("postcovid")
for f in ["outputs/placebo_summary.csv", "paper/tables/tab_window.tex"]:
    if not (ROOT / f).exists():
        fails.append(f)

raise SystemExit(1 if fails else print("TOATE CHECK-URILE TREC"))
