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

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Etichetele evenimentelor, in engleza, cu anul, ca sa nu confunde tur1_2024 cu
# tur1_2025 intr-un tabel. Sursa ramane events.csv, in romana; traducerea sta aici
# ca sa nu se strica daca se regenereaza tabelele.
EN = {
    "covid_urgenta_2020": "COVID state of emergency",
    "locale_2020": "Local elections 2020",
    "parlamentare_2020": "Parliamentary elections 2020",
    "demisie_orban_2020": "Orban resignation 2020",
    "guvern_citu_2020": "Citu I government formed",
    "criza_stelian_2021": "Stelian Ion crisis 2021",
    "motiune_citu_2021": "No-confidence motion 2021",
    "guvern_ciuca_2021": "Ciuca government formed 2021",
    "invazie_2022": "Russian invasion of Ukraine",
    "rotativa_ciolacu_2023": "Ciolacu rotation government 2023",
    "ipo_h2o_2023": "Hidroelectrica IPO listing 2023",
    "locale_euro_2024": "Local + European elections 2024",
    "tur1_2024": "Presidential first round 2024",
    "parlamentare_2024": "Parliamentary elections 2024",
    "ccr_anulare_2024": "Constitutional Court annulment 2024",
    "schengen_2024": "Schengen land accession 2024",
    "fitch_negativ_2024": "Fitch outlook to negative 2024",
    "guvern_ciolacu2_2024": "Ciolacu II government formed 2024",
    "bec_respinge_2025": "BEC rejects Georgescu 2025",
    "tur1_2025": "Presidential first round 2025",
    "demisie_ciolacu_2025": "Ciolacu resignation 2025",
    "tur2_2025": "Presidential second round 2025",
    "guvern_bolojan_2025": "Bolojan government formed 2025",
    "pachet_fiscal_2025": "Fiscal package (VAT rise) 2025",
}
TIP_EN = {"alegeri": "election", "guvern": "government", "ccr": "court",
          "ccr-alegeri": "court/election", "motiune": "no-confidence",
          "rating": "rating", "fiscal": "fiscal", "extern": "external",
          "sanatate": "health", "piata": "market"}
CONF_EN = {"ridicata": "high", "medie": "medium"}

def label(eid):
    return EN.get(eid, eid.replace("_", " "))

def fmt_date(x):
    d = pd.Timestamp(x)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"

def fmt_day(x):
    d = pd.Timestamp(x)
    return f"{d.day} {MONTHS[d.month - 1]}"

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
    s = pd.read_csv(OUT / "placebo_summary.csv").iloc[0]
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
        "FitchCar": num(p[p.event_id == "fitch_negativ_2024"].car3_tr.iloc[0]),
        "FitchP": num(p[p.event_id == "fitch_negativ_2024"].p_empilateric.iloc[0], 3),
        "NegMean": num(g[g.grup == "negativ"].mean_car3_tr.iloc[0]),
        "NegN": str(int(g[g.grup == "negativ"].n.iloc[0])),
        "TrioMean": num(t[t.event_id.isin(["tur1_2024", "parlamentare_2024", "tur1_2025"])].bet_car3.mean()),
        "TlvMay": num(r.loc["2025-05-05", "TLV"]), "BetMay": num(r.loc["2025-05-05", "BET"]),
        "BetFiMay": num(t[t.event_id == "tur1_2025"]["BET-FI_car3"].iloc[0]),
        "NEvents": str(len(t)),
        # testul agregat (nu sufera de multiplicitate)
        "AggP": num(s.p_agregat, 3), "AggPerm": str(int(s.p_perm)),
        "EvMeanAbs": num(s.ev_mean_abs), "NullMeanAbs": num(s.null_mean_abs),
        "AggObs": str(int(s.exceed_observed)), "AggExp": num(s.exceed_expected, 1),
        "AggN": str(int(s.n_events)),
        # sensibilitate la fereastra de estimare
        "RhoWindow": num(s.rho_fereastra_min, 3),
        "PqPostCovid": num(s.null_p95_postcovid),
        "NPfivePostCovid": str(int(s.n_p05_postcovid)),
    }
    # TeX citeste un control word doar pana la primul caracter non-litera, deci
    # \NullP95 ar fi parsat ca \NullP urmat de "95" -> undefined. Prindem aici.
    bad = [k for k in macros if not k.isalpha()]
    assert not bad, f"numele de macro TeX trebuie sa fie doar litere: {bad}"
    # \providecommand, nu \newcommand: un \input accidental de doua ori nu trebuie
    # sa facă compilarea să moară.
    write("macros.tex", "".join(
        f"\\providecommand{{\\{k}}}{{{v}}}\n" for k, v in macros.items()))

    # ---- tabel: evenimente ----------------------------------------------------
    rows = []
    for _, e in ev.iterrows():
        ed = t[t.event_id == e.event_id]
        d0 = fmt_date(ed.zi_tranzactionare.iloc[0]) if len(ed) else "--"
        rows.append(f"{label(e.event_id)} & {TIP_EN.get(e.tip, e.tip)} & "
                    f"{d0} & {CONF_EN.get(e.confidence, e.confidence)} \\\\")
    write("tab_events.tex",
          "\\begin{tabular}{lllc}\n\\toprule\nEvent & Type & Day 0 & Confidence \\\\\n"
          "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ---- tabel: efectele principale (BET, randament de pret) -------------------
    majors = ["tur1_2024", "parlamentare_2024", "ccr_anulare_2024", "tur1_2025", "tur2_2025"]
    rows = []
    for eid in majors:
        r_ = t[t.event_id == eid].iloc[0]
        d0 = fmt_day(r_.zi_tranzactionare)
        rows.append(f"{label(eid)} & {d0} & "
                    f"${num(r_.bet_ar0)}{stars(r_.bet_t0)}$ & "
                    f"${num(r_.bet_car3)}{stars(r_.bet_t3)}$ & "
                    f"${num(r_.bet_car11)}$ & ${num(r_.betx_car3)}$ \\\\")
    write("tab_main.tex",
          "{\\footnotesize\\setlength{\\tabcolsep}{3pt}\n"
          "\\begin{tabular}{lrrrrr}\n\\toprule\n"
          "Event & Day $0$ & $AR_0$ & CAR$[-1,+1]$ & CAR$[-5,+5]$ & Net STOXX \\\\\n"
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
        pat = {"2024-11-25": "instant shock, partial recovery",
               "2025-05-05": "degraded all day",
               "2025-05-19": "instant gain"}[shock]
        rows.append(f"{label(name)} & ${num(gap)}\\%$ & ${num(mn)}\\%$ ({tmin}) & "
                    f"${num(close)}\\%$ & {pat} \\\\")
    write("tab_speed.tex",
          "{\\footnotesize\\setlength{\\tabcolsep}{3.5pt}\n"
          "\\begin{tabular}{p{4.4cm}rrr p{3.4cm}}\n\\toprule\n"
          "Shock & Opening gap & Intraday low (local) & Close & Pattern \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

    # ---- tabel: comparatie indici (randament total) ---------------------------
    rows = []
    for eid in majors:
        r_ = t[t.event_id == eid].iloc[0]
        rows.append(f"{label(eid)} & ${num(r_.car3_tr)}$ & ${num(r_['ROTX_car3'])}$ & "
                    f"${num(r_['BET-FI_car3'])}$ & ${num(r_['BET-NG_car3'])}$ \\\\")
    write("tab_idx.tex",
          "\\begin{tabular}{lrrrr}\n\\toprule\n"
          "Event & BET-TR & ROTX & BET-FI & BET-NG \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

    # ---- tabel: placebo -------------------------------------------------------
    rows = []
    for _, r_ in p.head(7).iterrows():
        verdict = ("clears the null" if r_.p_empilateric < 0.05 else
                   "marginal" if r_.p_empilateric < 0.10 else "not significant")
        if r_.contaminat_dividend:
            verdict = "not significant (corrected: dividend)"
        rows.append(f"{label(r_.event_id)} & ${num(r_.car3_tr)}$ & "
                    f"${num(r_.t)}{stars(r_.t)}$ & ${num(r_.p_empilateric,3)}$ & {verdict} \\\\")
    write("tab_placebo.tex",
          "{\\footnotesize\\setlength{\\tabcolsep}{4pt}\n"
          "\\begin{tabular}{lrrrl}\n\\toprule\n"
          "Event & CAR$_3$ & conventional $t$ & empirical $p$ & Placebo verdict \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

    # ---- tabel: sensibilitate la fereastra de estimare -------------------------
    import analyze as A
    rows = []
    for w in A.WINDOWS:
        v = p[f"p_w{w[1]}"].dropna()
        hit = p.loc[v[v < 0.05].index, "event_id"].map(label)
        rows.append(f"$[{w[0]},\\;{-w[1]}]$ & {len(v)} & {len(hit)} & "
                    f"{', '.join(hit) if len(hit) else '--'} \\\\")
    write("tab_window.tex",
          "{\\footnotesize\\setlength{\\tabcolsep}{4pt}\n"
          "\\begin{tabular}{lrl p{9.6cm}}\n\\toprule\n"
          "Estimation window & $n$ & $p<0{,}05$ & Events \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

    print(f"OK -> paper/tables/ ({len(list(TAB.glob('*.tex')))} fisiere, {len(ev)} evenimente)")

if __name__ == "__main__":
    main()
