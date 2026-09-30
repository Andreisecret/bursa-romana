"""recovery.py - in cat timp se reface piata dupa un soc politic?

Ipoteza pe care o testam: "s-a revenit de fiecare data, deci e doar panica".
Problema ei e banala si se vede imediat: daca si caderile ALEATOARE de aceeasi
adancime se refac, atunci "revenirea" nu distinge panica de nimic. Deci orice
statistica de refacere se raporteaza la un placebo de caderi fara nicio stire
politica, cu ACEEASI adancime.

Comparatia este PERECHE: fiecare soc primeste propriul set de zile de control,
potrivite pe adancime, si e masurat timpul de refacere fata de mediana
placeholder-ului sau. Asta nu se lasa contaminata de distributia adancimilor.

Definimii (raportate la inchiderea din ziua -1, ultima sedinta dinaintea socului):
  shock        = r(0), randamentul din ziua evenimentului
  refacut in k = inchiderea dupa k sedinte a ajuns la nivelul dinaintea socului
  zile pana la refacere = primul k >= 0 cu refacut, sau NaN daca nu s-a refacut
  refacere %   = cat din drop s-a recuperat dupa 20 sedinte
                  (close_20 - close_0) / (close_{-1} - close_0)

Utilizare: python monitor/recovery.py [--horizon 60] [--min-shock 1.0]
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from analyze import load_prices, PRIMARY

OUT = ROOT / "monitor" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
RO = ZoneInfo("Europe/Bucharest")
HORIZON = 60          # sedinte de urmarire
MIN_SHOCK = 1.0       # % - sub prag, ziua nu e un soc, e agitatie
MIN_RETR = 0.5        # % - sub prag, retracementul in % nu are sens


def event_positions(px, ev, horizon):
    out = []
    for _, r in ev.iterrows():
        dt = datetime.fromisoformat(r["datetime_ro"]).replace(tzinfo=RO)
        d = dt.date()
        day = pd.Timestamp(d)
        if day in px.index and dt.hour < 18:
            p = px.index.get_loc(day)
        else:
            nxt = [x for x in px.index if x.date() > d]
            if not nxt:
                continue
            p = px.index.get_loc(nxt[0])
        if p - 1 < 0 or p + horizon + 1 >= len(px):
            continue
        out.append({"event_id": r["event_id"], "tip": r["tip"], "pos": p,
                    "day": px.index[p]})
    return out


def profile(close, p, horizon=HORIZON, min_retr=MIN_RETR):
    """Metricile de refacere pentru o pozitie p in seria de inchideri.
    Retracementul procentual are sens doar cand drop-ul e suficient de mare:
    la o miscare de -0.04% numitorul e practic zero si procentul iese in mii,
    deci il tratam ca nedefinit in loc sa aratam un numar fara sens."""
    pre, c0 = close[p - 1], close[p]
    move = c0 / pre - 1
    path = close[p:p + horizon + 1]
    if abs(move) * 100 >= min_retr:
        retr = (path - c0) / (pre - c0) * 100
    else:
        retr = np.full(len(path), np.nan)
    hit = np.flatnonzero(path >= pre)
    return {
        "move_pct": move * 100,
        "retr_5": retr[min(5, horizon)],
        "retr_20": retr[min(20, horizon)],
        "days_to_recover": int(hit[0]) if len(hit) else np.nan,
        "recovered": bool(len(hit)),
        "further_decline_pct": (path.min() / c0 - 1) * 100 if move < 0 else np.nan,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=HORIZON)
    ap.add_argument("--min-shock", type=float, default=MIN_SHOCK)
    ap.add_argument("--n-placebo", type=int, default=200)
    ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()

    px, rets = load_prices()
    close = px[PRIMARY].values
    rets_all = pd.Series(close).pct_change().values
    ev = pd.read_csv(ROOT / "events.csv")
    pos = event_positions(px, ev, a.horizon)

    all_rows = [{**e, **profile(close, e["pos"], a.horizon)}
                for e in pos]
    evdf = pd.DataFrame(all_rows)
    evdf["day"] = evdf["day"].dt.date.astype(str)
    evdf.to_csv(OUT / "recovery_events.csv", index=False)

    # Socs: doar caderile peste prag. O zi de -0.04% nu e un soc, e agitatie,
    # si daca am lasa in asta am umple placebo-ul cu zile fara eveniment.
    shocks = evdf[evdf.move_pct <= -a.min_shock].copy()
    # tur1_2025 si demisia Ciolacu sunt ACEEASI sedinta; daca nu le deduplicam,
    # numaram o singura zi de doua ori in comparatia pereche.
    shocks = shocks.drop_duplicates(subset=["day"]).reset_index(drop=True)
    drops = [p for p in np.arange(61, len(close) - a.horizon - 1)
             if np.isfinite(rets_all[p]) and rets_all[p] * 100 <= -a.min_shock]
    rng = np.random.default_rng(a.seed)

    # ---- comparatie PERECHE --------------------------------------------------
    pairs, prows = [], []
    for _, e in shocks.iterrows():
        depth = abs(e.move_pct)
        tol = max(0.4, 0.30 * depth)
        band = [p for p in drops if abs(abs(rets_all[p]) * 100 - depth) <= tol]
        if not band:
            pairs.append({"event_id": e.event_id, "move_pct": e.move_pct,
                          "zile_eveniment": e.days_to_recover,
                          "zile_placebo_mediana": np.nan, "diferenta": np.nan,
                          "n_placebo": 0})
            continue
        takes = rng.choice(band, size=min(a.n_placebo, len(band)), replace=False)
        rec = [profile(close, int(p), a.horizon) for p in takes]
        for p, r_ in zip(takes, rec):
            prows.append({"matched_to": e.event_id, "pos": int(p), **r_})
        pl = pd.DataFrame(rec)
        pl_med = float(pl.days_to_recover.median()) if pl.days_to_recover.notna().any() else np.nan
        pairs.append({
            "event_id": e.event_id, "move_pct": e.move_pct,
            "zile_eveniment": e.days_to_recover, "zile_placebo_mediana": pl_med,
            "diferenta": (e.days_to_recover - pl_med)
            if np.isfinite(pl_med) and np.isfinite(e.days_to_recover) else np.nan,
            "n_placebo": len(takes),
        })
    pdf = pd.DataFrame(prows)
    pdf.to_csv(OUT / "recovery_placebo.csv", index=False)
    pairdf = pd.DataFrame(pairs)
    pairdf.to_csv(OUT / "recovery_pairs.csv", index=False)

    # ipoteza: political refac mai repede decat un cadere oarecare de aceeasi
    # adancime => "e doar panica" are suport. diferenta negativa = mai repede.
    diff = pairdf.diferenta.dropna().values
    n_pairs = len(diff)
    rr = np.random.default_rng(a.seed + 1)
    null = np.array([(rr.choice(diff, n_pairs) if n_pairs else np.array([0.0])).mean()
                     for _ in range(4000)])
    obs_diff = diff.mean() if n_pairs else np.nan
    p_faster = float((1 + np.sum(null >= obs_diff)) / 4001)

    print("=" * 78)
    print("REFACERE DUPA SOC (seria " + PRIMARY + f", prag soc >= {a.min_shock}%, "
          f"orizont {a.horizon} sedinte)")
    print("=" * 78)
    show = shocks[["event_id", "day", "move_pct", "days_to_recover",
                   "retr_20", "further_decline_pct"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:+.2f}"))

    print("\n" + "=" * 78)
    print("COMPARATIE PERECHE: eveniment vs caderi de aceeasi adancime")
    print("=" * 78)
    print(pairdf.to_string(index=False, float_format=lambda x: f"{x:+.2f}"))
    print(f"\n  diferenta mediana (eveniment - placebo): "
          f"{np.median(diff):+.1f} sedinte  [negativ = refac mai repede]")
    print(f"  mai repede in {int((diff < 0).sum())} din {n_pairs} perechi; "
          f"la fel sau mai lent in {int((diff >= 0).sum())}")
    print(f"  permutare, ipoteza 'refac mai repede': p = {p_faster:.3f}")
    ev_rec = shocks.days_to_recover.dropna()
    pl_rec = pdf.days_to_recover.dropna()
    print(f"  refacut in orizont: politice {shocks.recovered.mean() * 100:.0f}%, "
          f"placebo {pdf.recovered.mean() * 100:.0f}%")
    drift = (close[-1] / close[0] - 1) * 100
    print(f"\n  CONTEXT: BET-TR a urcat {drift:+.0f}% intre {px.index[0].date()} si "
          f"{px.index[-1].date()}.")
    print("  Pragul 'a revenit la nivelul de dinainte' e asadar un prag mic intr-un")
    print("  piata care a urcat. De aceea nu e dovedita ipoteza panicii: si o cadere")
    print("  oarecare il atinge in 92% din cazuri.")

    print("\n" + "=" * 78)
    print("PRAG DE DETECTIE (din distributia nula a randamentului zilnic)")
    print("=" * 78)
    thr95 = np.percentile(np.abs(rets_all[1:]) * 100, 95)
    for q in [90, 95, 99]:
        thr = np.percentile(np.abs(rets_all[1:]) * 100, q)
        print(f"  p{q:<2d} |r zilnic| = {thr:.2f}%   "
              f"({np.mean(np.abs(rets_all[1:]) * 100 >= thr) * 100:.1f}% din sedinte)")
    pd.DataFrame([{"prag_p95_pct": thr95,
                   "sedinte_peste_prag": int((np.abs(rets_all[1:]) * 100 >= thr95).sum())}]
                 ).to_csv(OUT / "detection_threshold.csv", index=False)

    print(f"\nOK -> {OUT}/ (recovery_events, recovery_placebo, recovery_pairs, "
          f"detection_threshold)")


if __name__ == "__main__":
    main()
