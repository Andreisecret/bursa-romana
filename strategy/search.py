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

OUT = ROOT / "strategy" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
RO = ZoneInfo("Europe/Bucharest")
TRAIN_END = "2023-12-31"
HOLD = (-1, 1)


RULES = [
    ("pre_short_all",      None,            -1, "pre"),
    ("pre_long_all",       None,            +1, "pre"),
    ("open_short_all",     None,            -1, "open"),
    ("open_long_all",      None,            +1, "open"),
    ("pre_short_election", {"alegeri"},     -1, "pre"),
    ("pre_long_election",  {"alegeri"},     +1, "pre"),
    ("pre_short_guess",    {"alegeri", "ccr", "ccr-alegeri"}, -1, "pre"),
    ("pre_short_govt",     {"guvern", "motiune"}, -1, "pre"),
    ("pre_long_govt",      {"guvern", "motiune"}, +1, "pre"),
    ("overlay_all",        None,             0, "pre"),
    ("pre_short_elect_govt", {"alegeri", "guvern", "motiune", "ccr", "ccr-alegeri"}, -1, "pre"),
    ("pre_long_elect_govt",  {"alegeri", "guvern", "motiune", "ccr", "ccr-alegeri"}, +1, "pre"),
]


def positions(px, ev):
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
        if p - 1 < 0 or p + 2 >= len(px):
            continue
        out.append({"event_id": r["event_id"], "tip": r["tip"], "pos": p,
                    "day": px.index[p], "n_atr": 0})
    return out


def session_return(r, p, direction, entry, cost):


    if direction == 0:
        return 0.0
    if entry == "pre":
        a, b = p + HOLD[0], p + HOLD[1]
    else:
        a, b = p, p + HOLD[1]
    gross = float(np.prod(1 + direction * r[a:b + 1]) - 1)
    return gross - cost


def evaluate(r, positions_, rule, cost):
    _, tips, direction, entry = rule
    rets = []
    for e in positions_:
        if tips is not None and e["tip"] not in tips:
            continue
        rets.append(session_return(r, e["pos"], direction, entry, cost))
    return np.array(rets)


def tstat(v):
    if len(v) < 2 or v.std(ddof=1) == 0:
        return 0.0
    return float(v.mean() / (v.std(ddof=1) / np.sqrt(len(v))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-perm", type=int, default=5000)
    ap.add_argument("--cost-bps", type=float, default=50.0)
    ap.add_argument("--seed", type=int, default=17)
    a = ap.parse_args()

    px, _ = load_prices()
    r = px[PRIMARY].pct_change().fillna(0.0).values
    ev = pd.read_csv(ROOT / "events.csv")
    pos = positions(px, ev)
    train = [e for e in pos if str(e["day"].date()) <= TRAIN_END]
    test = [e for e in pos if str(e["day"].date()) > TRAIN_END]
    cost = a.cost_bps / 1e4

    print(f"reguli pre-declarate: {len(RULES)}   evenimente: {len(pos)} "
          f"(antrenament {len(train)} pana la {TRAIN_END}, test {len(test)})")
    print(f"costuri rotunde: {a.cost_bps:.0f} bps\n")

    rows = []
    obs_t = {}
    for rule in RULES:
        name = rule[0]
        tr = evaluate(r, train, rule, cost)
        te = evaluate(r, test, rule, cost)
        allv = evaluate(r, pos, rule, cost)
        obs_t[name] = tstat(allv)
        rows.append({"regula": name, "n_tr": len(tr), "n_te": len(te),
                     "medie_tr_pct": tr.mean() * 100 if len(tr) else np.nan,
                     "medie_te_pct": te.mean() * 100 if len(te) else np.nan,
                     "medie_toate_pct": allv.mean() * 100 if len(allv) else np.nan,
                     "t_toate": tstat(allv)})
    tab = pd.DataFrame(rows).sort_values("t_toate", ascending=False)
    tab.to_csv(OUT / "search_rules.csv", index=False)
    print("=" * 92)
    print("REGULI, ordonate dupa t pe intreaga perioada")
    print("=" * 92)
    print(tab.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))


    n_all = len(pos)
    lo, hi = 61, len(r) - 3
    offs = np.arange(HOLD[0], HOLD[1] + 1)
    rng = np.random.default_rng(a.seed)
    max_null = np.empty(a.n_perm)
    n_per_rule = {name: max(2, int(np.sum([1 for e in pos
                     if rule[1] is None or e["tip"] in rule[1]])))
                  for name, rule in zip([x[0] for x in RULES], RULES)}
    tradable = [r for r in RULES if r[2] != 0]
    for k in range(a.n_perm):
        best = -np.inf
        for rule in tradable:
            direction, entry = rule[2], rule[3]
            n_take = n_per_rule[rule[0]]
            picks = rng.integers(lo, hi, size=n_take)
            idx = picks[:, None] + (np.arange(0, 2) if entry == "open"
                                    else offs)[None, :]
            if entry == "open":
                idx = picks[:, None] + np.array([0, 1])[None, :]
            g = np.prod(1 + direction * r[idx], axis=1) - 1
            v = g - cost
            best = max(best, tstat(v))
        max_null[k] = best
    obs_t_tradable = {n: v for n, v in obs_t.items() if n in {r[0] for r in tradable}}
    obs_max = max(obs_t_tradable.values())
    n_tradable = len(tradable)
    degenerate = obs_max <= 0
    p_reality = float((1 + np.sum(max_null >= obs_max)) / (a.n_perm + 1))

    print("\n" + "=" * 92)
    print("REALITY CHECK (max-statistica peste cele "
          f"{n_tradable} reguli cu directie)")
    print("=" * 92)
    print(f"  cea mai buna t observata: {obs_max:.2f}  ({max(obs_t_tradable, key=obs_t_tradable.get)})")
    print(f"  max-statistica nula:    {max_null.mean():.2f} in medie, "
          f"p95 {np.percentile(max_null, 95):.2f}, max {max_null.max():.2f}")
    if degenerate:
        print(f"  p (reality check) = {p_reality:.4f} — DEGENERAT: cea mai buna t observata")
        print("  e negativa, deci orice maxim nul o depaseste. Testul nu poate distinge")
        print("  nimic; concluzia vine din faptul ca nicio regula nu are medie pozitiva.")
    else:
        print(f"  p (reality check) = {p_reality:.4f}")
    print(f"  sansa de a gasi ceva doar din noroc cu {n_tradable} reguli: "
          f"{(1 - 0.95 ** n_tradable) * 100:.0f}%")

    verdict = "supravietuieste" if p_reality < 0.05 else "NU supravietuieste"
    print(f"\n  VERDICT: {verdict} cautarii de regula cu {n_tradable} reguli tradabile.")


    tr_best = tab.iloc[0]
    print(f"\n  cea mai buna pe intreaga perioada: {tr_best.regula} "
          f"(train {tr_best.medie_tr_pct:+.2f}%, test {tr_best.medie_te_pct:+.2f}%)")
    if np.isfinite(tr_best.medie_te_pct) and tr_best.medie_te_pct < 0:
        print("  => semnul se inverseaza in afara sample-ului. Nu e o regula.")

    pd.DataFrame([{"reguli": len(RULES), "reguli_tradabile": n_tradable,
                   "t_max_observata": obs_max,
                   "max_null_mean": float(max_null.mean()),
                   "max_null_p95": float(np.percentile(max_null, 95)),
                   "p_reality": p_reality,                    "verdict": "degen" if degenerate else verdict,
                   "n_train": len(train), "n_test": len(test),
                   "cost_bps": a.cost_bps}]).to_csv(OUT / "search_reality.csv", index=False)
    print(f"\nOK -> {OUT}/ (search_rules.csv, search_reality.csv)")


if __name__ == "__main__":
    main()
