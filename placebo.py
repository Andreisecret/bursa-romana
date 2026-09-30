"""placebo.py — calibrarea care dicteaza concluzia studiului.

Importa estimatorul din analyze.py (`abnormal`), deci placebo-ul si studiul nu pot
divergea prin constructie. Ruleaza DUPA analyze.py.

Trei intrebari, trei teste:
 1. cat de mare este un CAR[-1,+1] obisnuit la BVB?      -> distributia nula
 2. care evenimente ies din ea?                           -> p empiric per eveniment
 3. evenimentele politice misca BET IN TOTAL?            -> test de permutare pe
    |CAR| mediu. Acesta e testul care nu sufera de
    multiplicitatea celor 24 de evenimente individuale.
Utilizare: python placebo.py [--n 500] [--seed 7] [--perm 20000]
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analyze import abnormal, PRIMARY, NEIGHBOUR, WINDOWS

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
POST_COVID = "2022-01-01"   # regimul fara restrictiile de turism 2020-21


def car3(rets, pos, est=(-60, -10)):
    return abnormal(rets, pos, est)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--perm", type=int, default=20000)
    a = ap.parse_args()

    px = pd.read_csv(DATA / "prices_daily.csv", parse_dates=["date"]).pivot(
        index="date", columns="ticker", values="close").sort_index()
    rets = px[PRIMARY].pct_change()
    n = len(rets)
    lo, hi = 60, n - 6                      # estimare completa + fereastra completa

    tab = pd.read_csv(OUT / "event_table.csv", parse_dates=["zi_tranzactionare"])
    blocked = set()
    for d in tab["zi_tranzactionare"]:
        p = rets.index.get_indexer([pd.Timestamp(d)], method="nearest")[0]
        blocked.update(range(p - NEIGHBOUR, p + NEIGHBOUR + 1))
    cand = [p for p in range(lo, hi) if p not in blocked]

    rng = np.random.default_rng(a.seed)
    picks = rng.choice(cand, size=min(a.n, len(cand)), replace=False)
    null = np.array([car3(rets, p) for p in picks])
    null = null[np.isfinite(null)]
    null_pct = null * 100
    pd.DataFrame({"pseudo_car3_tr_pct": null_pct}).to_csv(OUT / "placebo_null.csv", index=False)
    # cate o nula pentru fiecare fereastra de estimare (sensibilitate).
    # Ferestrele lungi necesita istoric: pentru evenimentele prea apropiate de
    # inceputul seriei coloanele de sensibilitate raman NaN, nu se taie fereastra.
    LO_SENS = -WINDOWS[0][0]
    cand_sens = [p for p in cand if p >= LO_SENS]
    null_alt = {w: np.array([car3(rets, p, w) for p in cand_sens]) for w in WINDOWS}
    null_alt = {w: v[np.isfinite(v)] for w, v in null_alt.items()}

    # ---- per eveniment: p empiric, sensibilitate la fereastra, regim post-COVID
    post = rets.index >= pd.Timestamp(POST_COVID)
    null_post = np.array([car3(rets, p) for p in picks if post[p]])   # in FRACTII
    null_post = null_post[np.isfinite(null_post)]
    p95_post = np.percentile(np.abs(null_post) * 100, 95)

    rows = []
    for _, r in tab.iterrows():
        d = r["zi_tranzactionare"]
        if d not in rets.index:
            continue
        pos = rets.index.get_loc(pd.Timestamp(d))
        if not (lo <= pos <= hi):
            continue
        c, t = abnormal(rets, pos)
        pv = (1 + np.sum(np.abs(null) >= abs(c))) / (len(null) + 1)
        pv_post = (1 + np.sum(np.abs(null_post) >= abs(c))) / (len(null_post) + 1)
        # aceeasi regula, cu ferestre de estimare alternante
        ok = pos >= LO_SENS
        alt = {f"car3_w{w[1]}": (round(car3(rets, pos, w) * 100, 2) if ok else np.nan)
               for w in WINDOWS}
        alt_p = {}
        for w in WINDOWS:
            alt_p[f"p_w{w[1]}"] = (
                (1 + np.sum(np.abs(null_alt[w]) >= abs(c))) / (len(null_alt[w]) + 1)
                if ok else np.nan)
        rows.append({"event_id": r["event_id"], "zi": d, "car3_tr": round(c * 100, 2),
                     "t": round(t, 2), "p_empilateric": round(pv, 4),
                     "p_postcovid": round(pv_post, 4),
                     "percentila_abs": round(100 * np.mean(np.abs(null) < abs(c)), 1),
                     "contaminat_dividend": r["contaminat_dividend"], **alt, **alt_p})
    res = pd.DataFrame(rows).sort_values("p_empilateric")
    res.to_csv(OUT / "placebo_results.csv", index=False)

    # ---- TEST AGREGAT: evenimentele politice misca BET in total? --------------
    # |CAR| mediu pe zilele de eveniment vs mostre aleatorii din null. Nu sufera
    # de multiplicitatea celor 24 de evenimente analizate unul cate unul.
    # Deduplicam zilele: tur1_2025 si demisia Ciolacu sunt aceeasi sedinta, iar
    # numararea ei de doua ori ar infla artificial gradul de dovezi.
    uniq = res.drop_duplicates(subset="zi")
    ev_car = uniq["car3_tr"].values
    pool = np.abs(null_pct)
    obs = np.abs(ev_car).mean()
    prng = np.random.default_rng(a.seed + 1)
    k = len(ev_car)
    draws = pool[prng.integers(0, len(pool), (a.perm, k))].mean(axis=1)
    p_agg = float((1 + np.sum(draws >= obs)) / (a.perm + 1))
    p95 = np.percentile(np.abs(null_pct), 95)
    expected_exceed = 0.05 * k
    observed_exceed = int((np.abs(ev_car) >= p95).sum())

    sens = {}
    for w in WINDOWS:
        col = f"p_w{w[1]}"
        v = res[col].dropna()
        sens[f"n_p05_w{w[1]}"] = int((v < 0.05).sum()) if len(v) else None
    # corelatia de rang intre ferestre: concluzia depinde de fereastra aleasa?
    # Spearman fara scipy = Pearson pe ranguri.
    wc = [f"car3_w{w[1]}" for w in WINDOWS]
    m = res[wc].rank().corr().values
    rank_rho = float(m[np.triu_indices(len(wc), k=1)].min())

    summary = {
        "n_null": len(null_pct), "null_mean": null_pct.mean(),
        "null_sd": null_pct.std(ddof=1), "null_p95": p95,
        "null_max": np.abs(null_pct).max(),
        "null_p95_postcovid": p95_post,
        "n_events": k, "ev_mean_abs": obs, "null_mean_abs": pool.mean(),
        "p_agregat": p_agg, "p_perm": a.perm,
        "exceed_observed": observed_exceed, "exceed_expected": expected_exceed,
        "n_p05_full": int((res.p_empilateric < 0.05).sum()),
        "n_p05_postcovid": int((res.p_postcovid < 0.05).sum()),
        "rho_fereastra_min": rank_rho,
        **sens,
    }
    pd.DataFrame([summary]).to_csv(OUT / "placebo_summary.csv", index=False)

    print(f"NULLA (N={len(null_pct)}, {PRIMARY}, vecinii evenimentelor exclusi)")
    print(f"  media {null_pct.mean():+.2f}% | sd {null_pct.std(ddof=1):.2f}% | "
          f"|CAR3| p95 {p95:.2f}% | max {summary['null_max']:.2f}%")
    print(f"  numai regimul post-COVID (din {POST_COVID}): p95 {p95_post:.2f}%\n")
    print(f"AGGREGAT (permutari iid din null, {a.perm} rulari, {k} zile distincte):")
    print(f"  |CAR| mediu pe zile de eveniment {obs:.2f}% vs {pool.mean():.2f}% pe zile oarecare")
    print(f"  p = {p_agg:.3f}   |   peste p95: {observed_exceed} observate "
          f"vs {expected_exceed:.1f} asteptate din sansa\n")
    print("SENSIBILITATE LA FERESTRA DE ESTIMARE:")
    for w in WINDOWS:
        v = res[f"p_w{w[1]}"].dropna()
        print(f"  estimare [{w[0]},-11]: p95 {np.percentile(np.abs(null_alt[w])*100,95):.2f}% | "
              f"evenimente p<0.05: {int((v<0.05).sum())} din {len(v)}")
    print(f"  corelatia de rang minima intre ferestre: rho = {rank_rho:.3f} "
          f"(1.0 = concluzia nu depinde de fereastra)")
    print(f"\n  p<0.05 pe null-ul complet: {summary['n_p05_full']}; "
          f"pe null-ul post-COVID: {summary['n_p05_postcovid']}\n")
    print(res.head(10).to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(null_pct, bins=40, color="#9bb", alpha=0.75, label=f"null (N={len(null_pct)})")
    ax.hist(np.abs(ev_car), bins=20, color="#d66", alpha=0.8,
            label=f"political event days (N={k})")
    for q, c in [(0.05, "orange"), (0.95, "orange")]:
        ax.axvline(np.quantile(null_pct, q), color=c, ls=":", lw=1, label="p5 / p95 of null")
    for _, r in res[res.p_empilateric < 0.05].iterrows():
        ax.axvline(abs(r["car3_tr"]), color="k", ls="--", lw=1.2)
        ax.text(abs(r["car3_tr"]), ax.get_ylim()[1] * 0.9, r["event_id"], rotation=90,
                fontsize=7, ha="right", va="top")
    ax.set_xlabel("|CAR[-1,+1]| %, BET-TR mean-adjusted")
    ax.set_ylabel("count")
    ax.set_title("Political event days against the null distribution\n"
                 f"{observed_exceed} events pass p95, {expected_exceed:.1f} expected "
                 f"by chance alone (aggregate p = {p_agg:.3f})")
    fig.tight_layout()
    fig.savefig(OUT / "fig_placebo.png", dpi=130)
    print("\nOK -> placebo_{null,results,summary}.csv + fig_placebo.png")


if __name__ == "__main__":
    main()
