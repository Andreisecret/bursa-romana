from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
RO = ZoneInfo("Europe/Bucharest")
STOCKS = ["TLV", "SNP", "BRD", "H2O", "SNG", "DIGI", "TEL", "SNN"]
INDICES = ["ROTX", "BET-TR", "BET-FI", "BET-NG"]
EST_LO, EST_HI = -60, -10
WINDOWS = [(-250, -10), (-120, -10), (-60, -10), (-40, -10)]
PRIMARY = "BET-TR"          # randament total; vezi caveat-ul despre dividende
NEIGHBOUR = 3               # excludem zilele apropiate de evenimente reale din nula

def abnormal(rets, pos, est=(EST_LO, EST_HI)):


    p = max(pos, -est[0])
    win = rets.iloc[p + est[0]:p + est[1]]
    car = float(rets.iloc[pos - 1:pos + 2].sum() - 3 * win.mean())
    sd = win.std()
    return car, (car / (sd * np.sqrt(3)) if sd and sd > 0 else np.nan)

def load_prices():
    df = pd.read_csv(DATA / "prices_daily.csv", parse_dates=["date"])
    px = df.pivot(index="date", columns="ticker", values="close").sort_index()
    rets = px.pct_change()
    bench = pd.read_csv(DATA / "bench_daily.csv", parse_dates=["date"]).set_index("date").sort_index()
    sx = bench["stoxx_close"].reindex(px.index).ffill()
    rets["STOXX"] = sx.pct_change()
    return px, rets

def event_day(ev_dt, trading_dates):


    d = ev_dt.date()
    if pd.Timestamp(d) in trading_dates and ev_dt.hour < 18:
        return pd.Timestamp(d)
    nxt = [x for x in trading_dates if x.date() > d]
    return nxt[0] if nxt else None

def ols_beta(y, x):
    m = np.isfinite(y) & np.isfinite(x)
    if m.sum() < 20:
        return 0.0, float(np.nanmean(y))
    X = np.vstack([np.ones(m.sum()), x[m]]).T
    coef, *_ = np.linalg.lstsq(X, y[m], rcond=None)
    return coef[1], coef[0]

def car_t(series_ar, pos, w, sd):
    seg = series_ar.iloc[pos + w[0]:pos + w[1] + 1]
    car = seg.sum()
    t = car / (sd * np.sqrt(len(seg))) if sd and sd > 0 else np.nan
    return car, t

def study(rets, ev_date):
    td = rets.index
    pos = td.get_loc(ev_date)
    if pos < 30:
        return None
    est = rets.iloc[max(0, pos - 60):pos - 10]
    out = {}

    mu, sd = est["BET"].mean(), est["BET"].std()
    ar_bet = rets["BET"] - mu
    for w, n, tn in [([0, 0], "ar0", "t0"), ([-1, 1], "car3", "t3"), ([-5, 5], "car11", "t11")]:
        c, t = car_t(ar_bet, pos, w, sd)
        out[f"bet_{n}"], out[f"bet_{tn}"] = c, t

    b, a = ols_beta(est["BET"].values, est["STOXX"].values)
    ar_bx = rets["BET"] - (a + b * rets["STOXX"])
    sd_bx = ar_bx.iloc[pos - 60:pos - 10].std()
    for w, n, tn in [([0, 0], "ar0", "t0"), ([-1, 1], "car3", "t3")]:
        c, t = car_t(ar_bx, pos, w, sd_bx)
        out[f"betx_{n}"], out[f"betx_{tn}"] = c, t
    out["stoxx_r0"] = rets["STOXX"].iloc[pos]
    out["divergenta"] = rets["BET"].iloc[pos] - rets["STOXX"].iloc[pos]

    for idx in INDICES:
        if idx not in rets:
            continue
        ar = rets[idx] - est[idx].mean()
        c, t = car_t(ar, pos, [-1, 1], est[idx].std())
        out[f"{idx}_car3"], out[f"{idx}_t3"] = c, t

    for s in STOCKS:
        if s not in rets or est[s].isna().all():
            continue
        bs, als = ols_beta(est[s].values, est["BET"].values)
        ar = rets[s] - (als + bs * rets["BET"])
        c, _ = car_t(ar, pos, [-1, 1], ar.iloc[pos - 60:pos - 10].std())
        out[f"{s}_car3"] = c
    return out

def main():
    px, rets = load_prices()
    ev = pd.read_csv(ROOT / "events.csv")
    rows = []
    for _, r in ev.iterrows():
        ev_dt = datetime.fromisoformat(r["datetime_ro"]).replace(tzinfo=RO)
        ed = event_day(ev_dt, px.index)
        if ed is None:
            continue
        try:
            s = study(rets, ed)
        except (KeyError, IndexError):
            continue
        if s is None:
            print(f"SKIP {r['event_id']}: istoric insuficient")
            continue
        tr3 = s.get("BET-TR_car3", np.nan)   # seria primara (randament total)
        contam = bool(np.isfinite(tr3) and abs(s["bet_car3"] - tr3) > 0.01)
        sig = abs(tr3) > 0.03 or (abs(s["bet_ar0"]) > 0.02 and not contam)
        rows.append({"event_id": r["event_id"], "anunt_ro": r["datetime_ro"],
                     "zi_tranzactionare": ed.date().isoformat(), "tip": r["tip"],
                     "confidence": r["confidence"], "scope": r["scope"],
                     "expected": r["expected"], "in_grup": r["in_grup"],
                     "bet_ar0": round(s["bet_ar0"] * 100, 2), "bet_t0": round(s["bet_t0"], 2),
                     "bet_car3": round(s["bet_car3"] * 100, 2), "bet_t3": round(s["bet_t3"], 2),
                     "bet_car11": round(s["bet_car11"] * 100, 2), "bet_t11": round(s["bet_t11"], 2),
                     "car3_tr": round(tr3 * 100, 2), "t3_tr": round(s.get("BET-TR_t3", np.nan), 2),
                     "contaminat_dividend": contam,
                     "betx_car3": round(s["betx_car3"] * 100, 2), "betx_t3": round(s["betx_t3"], 2),
                     "stoxx_r0": round(s["stoxx_r0"] * 100, 2),
                     "divergenta_ro_vs_eu": round(s["divergenta"] * 100, 2),
                     "semnificativ": bool(sig), **{
                     f"{t}_car3": round(s.get(f"{t}_car3", np.nan) * 100, 2)
                     for t in STOCKS + INDICES}})
    tab = pd.DataFrame(rows).sort_values("zi_tranzactionare")
    tab.to_csv(OUT / "event_table.csv", index=False)
    print(tab[["event_id", "zi_tranzactionare", "bet_car3", "car3_tr", "t3_tr",
               "contaminat_dividend", "betx_car3", "stoxx_r0"]].to_string(index=False))
    nc = tab[tab.contaminat_dividend]
    if len(nc):
        print(f"\nCONTAMINATE DIVIDEND: {list(nc.event_id)} "
              f"(exclus(e) din testul de grup)")


    grows = []
    for name, exp in [("negativ", "negativ"), ("pozitiv", "pozitiv")]:
        sub = tab[(tab.scope == "intern") & (tab.expected == exp)
                  & (tab.in_grup == "da") & (tab.confidence == "ridicata")
                  & (~tab.contaminat_dividend)]
        v = sub["car3_tr"].values
        m, t = (v.mean(), v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))) if len(v) > 1 else (v[0], np.nan)
        grows.append({"grup": name, "n": len(v), "mean_car3_tr": round(float(m), 2),
                      "t_cross_DESCRIPTIV": round(float(t), 2) if np.isfinite(t) else "",
                      "membri": ",".join(sub["event_id"].values),
                      "nota": "descriptiv; etichete ex-post, test circular"})
    gtab = pd.DataFrame(grows)
    gtab.to_csv(OUT / "group_test.csv", index=False)
    print("\n" + gtab.to_string(index=False))


    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(px.index, px["BET"], lw=1.2)
    for _, r in tab[tab.confidence == "ridicata"].iterrows():
        ax.axvline(pd.Timestamp(r["zi_tranzactionare"]), color="r", alpha=0.45, ls="--", lw=1)
    ax.set_title("BET 2020-2026 with political events (red lines = high confidence)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(OUT / "fig_bet_timeline.png", dpi=130)


    cars = {}
    for _, r in tab[tab.confidence == "ridicata"].iterrows():
        ed = pd.Timestamp(r["zi_tranzactionare"])
        pos = rets.index.get_loc(ed)
        mu = rets["BET"].iloc[pos - 60:pos - 10].mean()
        cars[r["event_id"]] = ((rets["BET"].iloc[pos - 5:pos + 6] - mu).cumsum() * 100).values
    if cars:
        fig2, ax2 = plt.subplots(figsize=(9, 5))
        for k, v in cars.items():
            ax2.plot(range(-5, 6), v, marker="o", ms=3, label=k)
        ax2.axhline(0, color="k", lw=0.8); ax2.axvline(0, color="k", ls=":", lw=0.8)
        ax2.set_xlabel("trading days from event (0 = event day)")
        ax2.set_ylabel("cumulative CAR % vs mean")
        ax2.set_title("Speed of the BET response: CAR [-5,+5] by event")
        ax2.legend(fontsize=7, ncol=2)
        fig2.tight_layout(); fig2.savefig(OUT / "fig_car_paths.png", dpi=130)


    base = px.index[1]
    fig3, ax3 = plt.subplots(figsize=(12, 4.5))
    ax3.plot(px.index, px["BET"] / px["BET"].loc[base] * 100, label="BET", lw=1.3)
    sx = pd.read_csv(DATA / "bench_daily.csv", parse_dates=["date"]).set_index("date").sort_index()
    sx = sx["stoxx_close"].reindex(px.index).ffill()
    ax3.plot(px.index, sx / sx.loc[base] * 100, label="STOXX600", lw=1.1, alpha=0.8)
    for _, r in tab[(tab.confidence == "ridicata") & (tab.semnificativ)].iterrows():
        ax3.axvline(pd.Timestamp(r["zi_tranzactionare"]), color="r", alpha=0.35, ls="--", lw=1)
    ax3.set_title("BET vs STOXX600 (2020-01=100): Romanian political shocks decouple from Europe")
    ax3.legend(); fig3.autofmt_xdate(); fig3.tight_layout()
    fig3.savefig(OUT / "fig_bet_vs_stoxx.png", dpi=130)


    majors = tab[tab.event_id.isin(["tur1_2024", "ccr_anulare_2024", "tur1_2025", "tur2_2025", "parlamentare_2024"])]
    if len(majors):
        cols = ["car3_tr", "ROTX_car3", "BET-FI_car3", "BET-NG_car3"]
        x = np.arange(len(majors)); w = 0.19
        fig4, ax4 = plt.subplots(figsize=(11, 4.5))
        for i, c in enumerate(cols):
            ax4.bar(x + i * w, majors[c].values, w, label=c.replace("_car3", ""))
        ax4.set_xticks(x + 1.5 * w); ax4.set_xticklabels(majors["event_id"].values, rotation=12, fontsize=8)
        ax4.set_ylabel("CAR[-1,+1] %"); ax4.axhline(0, color="k", lw=0.8)
        ax4.set_title("Who reacts hardest? BET vs ROTX vs financials (BET-FI) vs energy (BET-NG)")
        ax4.legend(fontsize=8); fig4.tight_layout()
        fig4.savefig(OUT / "fig_indices_car3.png", dpi=130)
    print(f"OK -> event_table.csv + group_test.csv + 4 figuri")

if __name__ == "__main__":
    main()
