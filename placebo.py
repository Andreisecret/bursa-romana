"""placebo.py — test placebo: distributia nula a CAR[-1,+1] pe zile pseudo-aleatoare.
Foloseste EXACT estimatorul din analyze.py (ajustare la medie, fereastra [-60,-11])
pe BET-TR (randament total), ca sa calibreze ce inseamna "miscare mare" la BVB.
Zilele din +/-3 sedii de orice eveniment real sunt excluse din nula, ca efectele
reale sa nuuble in null.
Utilizare: python placebo.py [--n 500] [--seed 7] -> outputs/placebo_{null,results}.csv + fig
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
PRIMARY = "BET-TR"      # vezi analyze.py: seria primara, imuna la ex-dividend
EST_LO, EST_HI = -60, -10
WIN = (-1, 1)
NEIGHBOUR = 3           # excludem zilele apropiate de evenimente reale


def car3(rets, pos):
    """CAR[-1,+1] cu ajustare la medie — identic cu analyze.study()."""
    est = rets.iloc[pos + EST_LO:pos + EST_HI]
    mu, sd = est.mean(), est.std()
    seg = rets.iloc[pos + WIN[0]:pos + WIN[1] + 1] - mu
    car = seg.sum()
    t = car / (sd * np.sqrt(3)) if sd > 0 else np.nan
    return car, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    px = pd.read_csv(DATA / "prices_daily.csv", parse_dates=["date"]).pivot(
        index="date", columns="ticker", values="close").sort_index()
    rets = px[PRIMARY].pct_change()
    n = len(rets)
    lo, hi = -EST_LO + 1, n - 6          # estimare completa + fereastra completa

    # zile reale (din tabel) si excluderea vecinilor
    tab = pd.read_csv(OUT / "event_table.csv", parse_dates=["zi_tranzactionare"])
    real_days = list(tab["zi_tranzactionare"])
    blocked = set()
    for d in real_days:
        p = rets.index.get_indexer([pd.Timestamp(d)], method="nearest")[0]
        blocked.update(range(p - NEIGHBOUR, p + NEIGHBOUR + 1))

    cand = [p for p in range(lo, hi) if p not in blocked]
    rng = np.random.default_rng(a.seed)
    picks = rng.choice(cand, size=min(a.n, len(cand)), replace=False)

    null = np.array([car3(rets, p)[0] for p in picks])
    null = null[np.isfinite(null)]
    # salvam in PROCENT (lizibil direct in CSV); toate pragurile de mai jos in pp
    null_pct = null * 100
    pd.DataFrame({"pseudo_car3_tr_pct": null_pct}).to_csv(OUT / "placebo_null.csv", index=False)

    # p-value empiric bilaterat pe |CAR3| pentru fiecare eveniment real
    rows = []
    for _, r in tab.iterrows():
        d = r["zi_tranzactionare"]
        if d not in rets.index:
            continue
        pos = rets.index.get_loc(pd.Timestamp(d))
        if not (lo <= pos <= hi):
            continue
        c, t = car3(rets, pos)
        pval = (1 + np.sum(np.abs(null) >= abs(c))) / (len(null) + 1)
        rows.append({"event_id": r["event_id"], "zi": d, "car3_tr": round(c * 100, 2),
                     "t": round(t, 2), "p_empilateric": round(pval, 4),
                     "percentila_abs": round(100 * np.mean(np.abs(null) < abs(c)), 1),
                     "contaminat_dividend": r["contaminat_dividend"]})
    res = pd.DataFrame(rows).sort_values("p_empilateric")
    res.to_csv(OUT / "placebo_results.csv", index=False)

    print(f"NULLA (N={len(null_pct)} pseudo-evenimente, BET-TR, excl. vecinii evenimentelor reale)")
    print(f"  media {null_pct.mean():+.2f}% | sd {null_pct.std(ddof=1):.2f}% | "
          f"|CAR3| p95 {np.percentile(np.abs(null_pct),95):.2f}% | max {np.abs(null_pct).max():.2f}%")
    print(f"  => la BVB un CAR[-1,+1] de 3% are frecventa ~"
          f"{100*np.mean(np.abs(null_pct) >= 3.0):.1f}% chiar fara nicio stire politica\n")
    print(res.head(10).to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(null_pct, bins=40, color="#9bb", alpha=0.75,
            label=f"nula (N={len(null_pct)} zile random)")
    for _, r in res[res.p_empilateric < 0.05].iterrows():
        ax.axvline(r["car3_tr"], color="r", ls="--", lw=1.2)
        ax.text(r["car3_tr"], ax.get_ylim()[1] * 0.92, r["event_id"], rotation=90,
                fontsize=7, ha="right", va="top")
    for q, c in [(0.05, "orange"), (0.95, "orange")]:
        ax.axvline(np.quantile(null_pct, q), color=c, ls=":", lw=1,
                   label="p5 / p95 nula")
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("CAR[-1,+1] % (BET-TR, ajustare la medie)")
    ax.set_ylabel("frecventa")
    ax.set_title("Test placebo: distributia nula vs evenimentele reale semnificative (p<0.05)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_placebo.png", dpi=130)
    print(f"\nOK -> placebo_null.csv, placebo_results.csv, fig_placebo.png")


if __name__ == "__main__":
    main()
