"""make_tables.py — genereaza tabelele si cifrele din date, ca paper.tex sa nu se
dezacordeze niciodata cu outputs/*.csv. Ruleaza DUPA analyze.py si placebo.py.
Utilizare: python make_tables.py -> paper/tables/*.tex  (apoi pdflatex de 2x)
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
TAB = ROOT / "paper" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

def num(x, d=2):
    """numar pentru LaTeX. Semnul minus ramane real (corect in matematica),
    virgula zecimala se forțeaza cu {,} pentru a evita spatierea din math mode."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    return f"{x:.{d}f}".replace(".", "{,}")

LUNI = ["ian", "feb", "mar", "apr", "mai", "iun",
        "iul", "aug", "sep", "oct", "noi", "dec"]

def date_ro(x):
    d = pd.Timestamp(x)
    return f"{d.day} {LUNI[d.month - 1]} {d.year}"

def date_short(x):
    d = pd.Timestamp(x)
    return f"{d.day} {LUNI[d.month - 1]}"

def stars(t):
    if not np.isfinite(t):
        return ""
    return "^{**}" if abs(t) > 2.58 else ("^{*}" if abs(t) > 1.96 else "")

def write(name, body):
    (TAB / name).write_text(body, encoding="utf-8")
    print(f"  {name}")

def main():
    t = pd.read_csv(OUT / "event_table.csv", parse_dates=["zi_tranzactionare"])
    p = pd.read_csv(OUT / "placebo_results.csv")
    g = pd.read_csv(OUT / "group_test.csv")
    ev = pd.read_csv(ROOT / "events.csv")
    intra = pd.read_csv(ROOT / "data" / "intraday_15m.csv", parse_dates=["ts_ro"])
    null = pd.read_csv(OUT / "placebo_null.csv")["pseudo_car3_tr_pct"]

    # ---- cifrele din prose (macros) -------------------------------------------
    sd = null.std(ddof=1); p95 = np.percentile(null.abs(), 95)
    freq3 = 100 * np.mean(null.abs() >= 3.0)
    px = pd.read_csv(ROOT / "data" / "prices_daily.csv", parse_dates=["date"]).pivot(
        index="date", columns="ticker", values="close").sort_index()
    r = px.pct_change() * 100
    sx = pd.read_csv(ROOT / "data" / "bench_daily.csv", parse_dates=["date"]).set_index("date").sort_index()
    sxf = sx["stoxx_close"].reindex(px.index).ffill().pct_change() * 100
    loc = t[t.event_id == "locale_euro_2024"].iloc[0]
    macros = {
        "NullSd": num(sd), "NullPqfive": num(p95), "NullMax": num(null.abs().max()),
        "NullFreqThree": num(freq3, 1),
        "TurTwoCar": num(p[p.event_id == "tur2_2025"].car3_tr.iloc[0]),
        "TurTwoP": num(p[p.event_id == "tur2_2025"].p_empilateric.iloc[0], 3),
        "TurTwoPct": num(p[p.event_id == "tur2_2025"].percentila_abs.iloc[0], 1),
        "ParlCar": num(p[p.event_id == "parlamentare_2024"].car3_tr.iloc[0]),
        "ParlP": num(p[p.event_id == "parlamentare_2024"].p_empilateric.iloc[0], 3),
        "TurOneCar": num(p[p.event_id == "tur1_2025"].car3_tr.iloc[0]),
        "TurOneP": num(p[p.event_id == "tur1_2025"].p_empilateric.iloc[0], 3),        "CiucaCar": num(p[p.event_id == "guvern_ciuca_2021"].car3_tr.iloc[0]),
        "CiucaP": num(p[p.event_id == "guvern_ciuca_2021"].p_empilateric.iloc[0], 3),
        "CiucaT": num(p[p.event_id == "guvern_ciuca_2021"].t.iloc[0]),
        "CiucaStoxx": num(sxf.loc["2021-11-26"]), "CiucaBet": num(r.loc["2021-11-26", "BET"]),
        "CiucaInvestDay": num(r.loc["2021-11-25", "BET"]),
        "LocaleBet": num(loc.bet_car3), "LocaleTr": num(loc.car3_tr),
        "LocaleT": num(t[t.event_id == "locale_euro_2024"].bet_t3.iloc[0]),
        "CcrCar": num(p[p.event_id == "ccr_anulare_2024"].car3_tr.iloc[0]),
        "CcrP": num(p[p.event_id == "ccr_anulare_2024"].p_empilateric.iloc[0], 3),
        "CcrArZero": num(t[t.event_id == "ccr_anulare_2024"].bet_ar0.iloc[0]),
        "NegMean": num(g[g.grup == "negativ"].mean_car3_tr.iloc[0]),
        "NegN": str(int(g[g.grup == "negativ"].n.iloc[0])),
        "TrioMean": num(t[t.event_id.isin(["tur1_2024", "parlamentare_2024", "tur1_2025"])].bet_car3.mean()),
        "TlvMay": num(r.loc["2025-05-05", "TLV"]), "BetMay": num(r.loc["2025-05-05", "BET"]),
        "BetFiMay": num(t[t.event_id == "tur1_2025"]["BET-FI_car3"].iloc[0]),
        "NEvents": str(len(t)),
    }
    # TeX citeste un control word doar pana la primul caracter non-litera, deci
    # \NullP95 ar fi parsat ca \NullP urmat de "95" -> undefined. Prindem aici.
    bad = [k for k in macros if not k.isalpha()]
    assert not bad, f"numele de macro TeX trebuie sa fie doar litere: {bad}"
    write("macros.tex", "".join(
        f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in macros.items()))

    # ---- tabel: evenimente ----------------------------------------------------
    rows = []
    for _, e in ev.iterrows():
        ed = t[t.event_id == e.event_id]
        d0 = date_ro(ed.zi_tranzactionare.iloc[0]) if len(ed) else "--"
        rows.append(f"{e.event_id.split('_')[0].replace('_',' ')} & {e.tip} & "
                    f"{d0} & {e.confidence} \\\\")
    write("tab_events.tex",
          "\\begin{tabular}{lllc}\n\\toprule\nEveniment & Tip & Ziua 0 & Încredere \\\\\n"
          "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ---- tabel: efectele principale (BET, randament de pret) -------------------
    majors = ["tur1_2024", "parlamentare_2024", "ccr_anulare_2024", "tur1_2025", "tur2_2025"]
    rows = []
    for eid in majors:
        r_ = t[t.event_id == eid].iloc[0]
        d0 = date_short(r_.zi_tranzactionare)
        rows.append(f"{eid.replace('_',' ')} & {d0} & "
                    f"${num(r_.bet_ar0)}{stars(r_.bet_t0)}$ & "
                    f"${num(r_.bet_car3)}{stars(r_.bet_t3)}$ & "
                    f"${num(r_.bet_car11)}$ & ${num(r_.betx_car3)}$ \\\\")
    write("tab_main.tex",
          "{\\footnotesize\\setlength{\\tabcolsep}{3pt}\n"
          "\\begin{tabular}{lrrrrr}\n\\toprule\n"
          "Eveniment & Ziua $0$ & $AR_0$ & CAR$[-1,+1]$ & CAR$[-5,+5]$ & Net STOXX \\\\\n"
          "\\midrule\n" + "\n".join(rows) +
          "\n\\bottomrule\n\\end{tabular}}\n")

    # ---- tabel: viteza intraday ----------------------------------------------
    SHOCKS = {"2024-11-25": "tur1_2024", "2025-05-05": "tur1_2025", "2025-05-19": "tur2_2025"}
    rows = []
    for shock, name in SHOCKS.items():
        b = intra[intra.window == name]
        b = b[b.ticker == "BET"].sort_values("ts_ro")
        pre = b[pd.to_datetime(b.ts_ro).dt.date.astype(str) < shock].close.iloc[-1]
        d0 = b[pd.to_datetime(b.ts_ro).dt.date.astype(str) == shock]
        gap = (d0.close.iloc[0] / pre - 1) * 100
        mn = (d0.close.min() / pre - 1) * 100
        tmin = pd.Timestamp(d0.loc[d0.close.idxmin(), "ts_ro"]).strftime("%H:%M")
        close = (d0.close.iloc[-1] / pre - 1) * 100
        pat = {"2024-11-25": "șoc instant + recuperare",
               "2025-05-05": "degradare toată ziua",
               "2025-05-19": "câștig instant"}[shock]
        rows.append(f"{name.replace('_',' ')} & ${num(gap)}\\%$ & ${num(mn)}\\%$ ({tmin}) & "
                    f"${num(close)}\\%$ & {pat} \\\\")
    write("tab_speed.tex",
          "{\\small\\setlength{\\tabcolsep}{4pt}\n"
          "\\begin{tabular}{lrrrl}\n\\toprule\n"
          "Șoc & Gap open & Minim (ora RO) & Închidere & Tipar \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

    # ---- tabel: comparatie indici (randament total) ---------------------------
    rows = []
    for eid in majors:
        r_ = t[t.event_id == eid].iloc[0]
        rows.append(f"{eid.replace('_',' ')} & ${num(r_.car3_tr)}$ & ${num(r_['ROTX_car3'])}$ & "
                    f"${num(r_['BET-FI_car3'])}$ & ${num(r_['BET-NG_car3'])}$ \\\\")
    write("tab_idx.tex",
          "\\begin{tabular}{lrrrr}\n\\toprule\n"
          "Eveniment & BET-TR & ROTX & BET-FI & BET-NG \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ---- tabel: placebo -------------------------------------------------------
    rows = []
    for _, r_ in p.head(7).iterrows():
        verdict = ("se separă de null" if r_.p_empilateric < 0.05 else
                   "marginal" if r_.p_empilateric < 0.10 else "nesemnificativ")
        if r_.contaminat_dividend:
            verdict = "nesemnificativ (corectat: dividend)"
        rows.append(f"{r_.event_id.replace('_',' ')} & ${num(r_.car3_tr)}$ & "
                    f"${num(r_.t)}{stars(r_.t)}$ & ${num(r_.p_empilateric,3)}$ & {verdict} \\\\")
    write("tab_placebo.tex",
          "{\\footnotesize\\setlength{\\tabcolsep}{4pt}\n"
          "\\begin{tabular}{lrrrl}\n\\toprule\n"
          "Eveniment & CAR$_3$ & $t$ clasic & $p$ empiric & Verdict placebo \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

    print(f"OK -> paper/tables/ ({len(list(TAB.glob('*.tex')))} fisiere, {len(ev)} evenimente)")

if __name__ == "__main__":
    main()
