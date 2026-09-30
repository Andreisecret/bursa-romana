import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from analyze import load_prices, abnormal, PRIMARY
from fetch_intraday import WINDOWS

OUT = ROOT / "strategy" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data"


FORBIDDEN = {"expected", "semnificativ", "contaminat_dividend", "bet_car3",
             "car3_tr", "t3_tr", "bet_t3", "p_empilateric", "percentila_abs"}
HOLD = (-1, 1)


def load():
    px, rets = load_prices()
    ev = pd.read_csv(ROOT / "events.csv")
    vol = (pd.read_csv(DATA / "prices_daily.csv", parse_dates=["date"])
           .query("ticker != 'BET'")
           .pivot(index="date", columns="ticker", values="volume").sum(axis=1))
    return px, rets, ev, vol


def event_positions(px, ev, min_liq=None):


    from datetime import datetime
    from zoneinfo import ZoneInfo
    ro = ZoneInfo("Europe/Bucharest")
    out = []
    for _, r in ev.iterrows():
        dt = datetime.fromisoformat(r["datetime_ro"]).replace(tzinfo=ro)
        d = dt.date()
        day = pd.Timestamp(d)
        if day in px.index and dt.hour < 18:
            p = px.index.get_loc(day)
        else:
            nxt = [x for x in px.index if x.date() > d]
            if not nxt:
                continue
            p = px.index.get_loc(nxt[0])
        if p - 1 < 0 or p + 2 >= len(px):
            continue
        if min_liq is not None and vol_ok(vol, px.index[p], min_liq) is False:
            continue
        out.append({"event_id": r["event_id"], "tip": r["tip"], "pos": p,
                    "day": px.index[p]})
    return out


def vol_ok(vol, day, min_liq):
    return float(vol.get(day, 0.0)) >= min_liq


def trade_returns(rets, positions, cost_bps, direction):


    r = rets[PRIMARY].values
    cost = cost_bps / 1e4
    out = []
    for e in positions:
        p = e["pos"]
        a, b = p + HOLD[0], p + HOLD[1]
        gross = float(np.prod(1 + direction * r[a:b + 1]) - 1)
        out.append({**e, "gross": gross, "net": gross - cost})
    return pd.DataFrame(out)


def stats(df, label):
    if len(df) == 0:
        return {"strategy": label, "n": 0}
    v = df["net"].values
    return {"strategy": label, "n": len(v),
            "mean_net_pct": v.mean() * 100, "median_net_pct": np.median(v) * 100,
            "sd_pct": v.std(ddof=1) * 100 if len(v) > 1 else np.nan,
            "win_rate": float((v > 0).mean()),
            "sum_net_pct": v.sum() * 100}


def bootstrap_ci(v, n_boot, seed):
    r = np.random.default_rng(seed)
    means = r.choice(v, size=(n_boot, len(v)), replace=True).mean(axis=1) * 100
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def placebo_distribution(rets, n_draw, cost_bps, direction, n_pos, seed):


    r = rets[PRIMARY].values
    cost = cost_bps / 1e4
    rr = np.random.default_rng(seed)
    lo, hi = 61, len(r) - 3
    picks = rr.integers(lo, hi, size=(n_draw, n_pos))
    offs = np.arange(HOLD[0], HOLD[1] + 1)
    idx = picks[:, :, None] + offs[None, None, :]
    gross = np.prod(1 + direction * r[idx], axis=2) - 1
    return gross.mean(axis=1) * 100 - cost * 100


def gap_capturable(intraday, rets):


    rows = []
    for name, (_, _, shock) in WINDOWS.items():
        sub = intraday[intraday.window == name]
        b = sub[sub.ticker == "BET"].sort_values("ts_ro").copy()
        b["d"] = pd.to_datetime(b["ts_ro"]).dt.date.astype(str)
        pre = b[b["d"] < shock]["close"].iloc[-1]
        d0 = b[b["d"] == shock]
        if len(d0) == 0:
            continue
        gap = d0["close"].iloc[0] / pre - 1
        day = d0["close"].iloc[-1] / pre - 1
        car3, _ = abnormal(rets[PRIMARY], rets.index.get_loc(pd.Timestamp(shock)))
        rows.append({"shock": name,
                     "gap_open_pct": gap * 100,
                     "day_close_pct": day * 100,
                     "car3_pct": car3 * 100,
                     "gap_share_of_car_pct": abs(gap / car3) * 100 if abs(car3) > 1e-9 else np.nan,
                     "left_after_news_pct": (car3 - gap) * 100})
    return pd.DataFrame(rows)


def equity_overlay(px, positions, exposure_off=True):


    r = px[PRIMARY].pct_change().fillna(0.0)
    mask_off = pd.Series(False, index=r.index)
    for e in positions:
        p = e["pos"]
        a, b = p + HOLD[0], p + HOLD[1]
        mask_off.iloc[max(0, a):min(len(r), b + 1)] = True
    mask_off = mask_off if exposure_off else ~mask_off
    strat = r.where(~mask_off, 0.0)
    eq_bh, eq_s = (1 + r).cumprod(), (1 + strat).cumprod()

    def dd(eq):
        return float((eq / eq.cummax() - 1).min() * 100)

    def rets_stats(eq):
        rr = eq.pct_change().dropna()
        vol = rr.std(ddof=1) * np.sqrt(252) * 100
        return {"total_pct": float((eq.iloc[-1] - 1) * 100), "ann_vol_pct": vol,
                "sharpe": float(rr.mean() / rr.std(ddof=1) * np.sqrt(252)) if rr.std(ddof=1) > 0 else np.nan,
                "max_dd_pct": dd(eq)}

    return {"buy_and_hold": rets_stats(eq_bh), "event_overlay": rets_stats(eq_s),
            "event_days": int(mask_off.sum())}


def overlay_placebo(px, positions, n_draw, seed):


    r = px[PRIMARY].pct_change().fillna(0.0)
    idx = [e["pos"] for e in positions]
    n_sessions = len(r)
    off = np.zeros(n_sessions, dtype=bool)
    for p in idx:
        off[max(0, p + HOLD[0]):min(n_sessions, p + HOLD[1] + 1)] = True
    n_off = int(off.sum())
    rr = np.random.default_rng(seed)
    out = []
    for _ in range(n_draw):
        fake = np.zeros(n_sessions, dtype=bool)
        for s in rr.integers(2, n_sessions - 3, size=n_off):
            fake[s - 1:s + 2] = True
        eq = (1 + r.where(~fake, 0.0)).cumprod()
        rets_eq = eq.pct_change().dropna()
        if rets_eq.std(ddof=1) == 0:
            continue
        out.append((rets_eq.mean() / rets_eq.std(ddof=1) * np.sqrt(252),
                    float((eq / eq.cummax() - 1).min() * 100)))
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost-bps", type=float, default=50.0, help="costuri rotunde, bps")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--n-draw", type=int, default=2000)
    ap.add_argument("--min-liq", type=float, default=0.0, help="prag volum (lei)")
    a = ap.parse_args()

    px, rets, ev, vol = load()
    pos_all = event_positions(px, ev, min_liq=a.min_liq or None)


    intraday = pd.read_csv(DATA / "intraday_15m.csv")
    gapdf = gap_capturable(intraday, rets)
    gapdf.to_csv(OUT / "gap_capturable.csv", index=False)


    ELECTIONS = {"alegeri"}
    pos_el = [p for p in pos_all if p["tip"] in ELECTIONS]
    rows = []
    for label, ps, direction in [("S1 short ALL events", pos_all, -1),
                                 ("S1 long ALL events", pos_all, +1),
                                 ("S1 short elections only", pos_el, -1),
                                 ("S1 long elections only", pos_el, +1)]:
        df = trade_returns(rets, ps, a.cost_bps, direction)
        if len(df) == 0:
            continue
        s = stats(df, label)
        s["ci95_lo"], s["ci95_hi"] = bootstrap_ci(df["net"].values, a.boot, 7)
        pl = placebo_distribution(rets, a.n_draw, a.cost_bps, direction, len(df), 11)
        s["placebo_mean_pct"] = pl.mean()
        s["p_vs_placebo"] = float((1 + np.sum(np.abs(pl) >= abs(df["net"].mean() * 100)))
                                   / (len(pl) + 1))
        rows.append(s)
    s1 = pd.DataFrame(rows)
    s1.to_csv(OUT / "s1_directional.csv", index=False)


    s2 = equity_overlay(px, pos_all, exposure_off=True)
    pd.DataFrame([s2["buy_and_hold"], s2["event_overlay"]]).to_csv(OUT / "s2_overlay.csv")
    pl2 = overlay_placebo(px, pos_all, a.n_draw, 13)
    s2_p = {
        "sharpe_observed": s2["event_overlay"]["sharpe"],
        "sharpe_placebo_p95": float(np.percentile(pl2[:, 0], 95)),
        "sharpe_placebo_max": float(pl2[:, 0].max()),
        "maxdd_observed": s2["event_overlay"]["max_dd_pct"],
        "maxdd_placebo_p05": float(np.percentile(pl2[:, 1], 5)),
        "n_draw": len(pl2),
    }
    pd.DataFrame([s2_p]).to_csv(OUT / "s2_placebo.csv", index=False)


    print("=" * 78)
    print("D0  CAT DIN MISCARE E CAPTURABILA DUPA VESTE")
    print("=" * 78)
    print(gapdf.to_string(index=False, float_format=lambda x: f"{x:+.2f}"))
    print("\n  gap_share_of_car = cat la deschidere din miscarea pe 3 sedinte.")
    print("  left_after_news  = ce ar mai putea lua cine reactioneaza LA stire,")
    print("  dupa ce aceasta e deja publicata si pretul a sarit.\n")

    print("=" * 78)
    print(f"S1  STRATEGIE DIRECTIONALA  (costuri rotunde {a.cost_bps:.0f} bps)")
    print("=" * 78)
    print(s1.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))

    print("\n" + "=" * 78)
    print("S2  OVERLAY DE RISC (expunere 0 in ferestrele de eveniment)")
    print("=" * 78)
    for k in ["buy_and_hold", "event_overlay"]:
        d = s2[k]
        print(f"  {k:16s} total {d['total_pct']:+7.2f}%  vol {d['ann_vol_pct']:5.2f}%  "
              f"Sharpe {d['sharpe']:5.2f}  maxDD {d['max_dd_pct']:7.2f}%")
    print(f"  (sedi de expunere 0: {s2['event_days']} din {len(px)})")
    print(f"\n  PLACEBO, aceleasi {s2['event_days']} sedii scoase la intamplare "
          f"({s2_p['n_draw']} desene):")
    print(f"    Sharpe 95th percentile {s2_p['sharpe_placebo_p95']:.2f}, "
          f"max {s2_p['sharpe_placebo_max']:.2f}   |   observat {s2_p['sharpe_observed']:.2f}")
    print(f"    maxDD 5th percentile  {s2_p['maxdd_placebo_p05']:.2f}   "
          f"|   observat {s2_p['maxdd_observed']:.2f}")
    print("    Daca observatul e in interiorul distributiei, imbunatatirea vine din")
    print("    faptul ca am ales ferestrele care au cazut, nu din regula insasi.")

    print(f"\nOK -> {OUT}/ (gap_capturable.csv, s1_directional.csv, s2_overlay.csv, s2_placebo.csv)")


if __name__ == "__main__":
    main()
