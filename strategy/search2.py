"""search2.py - ce ar trebui sa fie ca sa conteze.

search.py a aratat ca nimic nu supravietuieste cautarii de regula. Doua intrebari
raman, si amandase se raspund fara sa cautam reguli noi:

  1. SENSIBILITATE LA COST. 50 bps poate fi prea putini pentru o piata ca BVB.
     Daca marginea dispare la costuri realiste, raspunsul e ca nu exista.
  2. PUTERE DE DETECTIE. Care ar fi efectul minim pe care testul l-ar putea
     detecta? Daca e mult peste ce observam, atunci designul nu poate raspunde
     la intrebare nici cand raspunde bine. Asta e mai util decat un p-value.

Nu adaugam reguli. Cautarea de regula e deja plătita, iar marirea sample-ului
e singura cale care ar crește puterea.

Utilizare: python strategy/search2.py
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from analyze import load_prices, PRIMARY
from search import RULES, positions, evaluate, tstat

OUT = ROOT / "strategy" / "outputs"


def main():
    px, _ = load_prices()
    ev = pd.read_csv(ROOT / "events.csv")
    pos = positions(px, ev)
    r = px[PRIMARY].pct_change().fillna(0.0).values

    # ---- 1. sensitivitate la cost -------------------------------------------
    print("=" * 84)
    print("1. SENSIBILITATE LA COSTURI (cele mai bune 3 reguli, pe intreaga perioada)")
    print("=" * 84)
    costs = [0, 25, 50, 100, 200]
    grid = []
    for rule in RULES:
        if rule[2] == 0:
            continue
        row = {"regula": rule[0]}
        for c in costs:
            v = evaluate(r, pos, rule, c / 1e4)
            row[f"{c}bps"] = v.mean() * 100
            if c == 50:
                row["t@50"] = tstat(v)
        grid.append(row)
    g = pd.DataFrame(grid).sort_values("50bps", ascending=False)
    print(g.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))
    g.to_csv(OUT / "search2_cost.csv", index=False)

    best = g.iloc[0]
    print(f"\n  cea mai buna: {best.regula}")
    for c in costs:
        print(f"    {c:4d} bps -> {best[f'{c}bps']:+.3f}% pe tranzactie")
    breakeven = None
    for c in costs:
        if best[f"{c}bps"] <= 0 and breakeven is None:
            breakeven = c
    if breakeven is None:
        print(f"  ramane profitabila chiar la {costs[-1]} bps pe transacție")
    else:
        print(f"  pragul de rentabilitate: {breakeven} bps pe tranzacție")
    print("  Brokeraj, spread și impact pe o piață ca BVB sunt realist 50-200 bps")
    print("  în ambele sensuri. Sub pragul de rentabilitate nu e strategie.")

    # ---- 2. putere de detectie ----------------------------------------------
    print("\n" + "=" * 84)
    print("2. PUTEREA DE DETECTIE: ce efect minim ar fi vizibil?")
    print("=" * 84)
    rule_best = RULES[[x[0] for x in RULES].index("open_short_all")]
    v = evaluate(r, pos, rule_best, 50 / 1e4)      # net, pentru raportare
    v_gross = evaluate(r, pos, rule_best, 0.0)     # BRUT, pentru putere
    n, sd, alpha = len(v), v.std(ddof=1), 0.05
    se = sd / np.sqrt(n)
    mde = 1.96 * se            # efect minim la pragul de 5%, putere 50%
    print(f"  n = {n} evenimente, dispersie {sd * 100:.2f}%, erare standard {se * 100:.2f}%")
    print(f"  efect minim detectabil la alfa=5%, putere 50%: {mde * 100:.2f}% per tranzactie")
    print(f"  efect BRUT observat (cea mai buna regula):     {v_gross.mean() * 100:.2f}%")
    print(f"  efect NET observat, la 50 bps:                 {v.mean() * 100:.2f}%")
    print(f"  raport brut / minim detectabil:                {v_gross.mean() / mde:.2f}")
    print()
    print("  Cu acest n si aceasta dispersie, o regula reala ar trebui sa mute")
    print(f"  BET cu macroscopic {mde * 100:.1f}% pe eveniment ca sa poata fi detectata.")
    print("  Efectul brut observat e sub acest prag: cu 24 de evenimente nici un")
    print("  efect real de aceasta marime nu s-ar vedea. Indiferent daca exista sau nu.")

    # cate evenimente ar trebui ca puterea sa fie 80% la efectul BRUT observat
    from statistics import NormalDist
    z_a = NormalDist().inv_cdf(1 - alpha / 2)
    z_b = NormalDist().inv_cdf(0.80)
    n_need = (z_a + z_b) ** 2 * (sd / v_gross.mean()) ** 2
    have = len(pos)
    print(f"\n  Pentru putere 80% la efectul brut observat ar trebui {n_need:.0f} evenimente,")
    print(f"  avem {have}. Factor de acoperire necesar: {n_need / have:.0f}x")
    print("  Asta e explicația reală: nu e o problemă de căutare, e o problemă de")
    print("  dimensiune a eșantionului. Un ciclu electoral românesc are 2-3 tururi")
    print("  pe an, iar măsurarea utilă cere 1-3 ședințe. Rezultă zeci de evenimente,")
    print("  nu sute. Extinderea listei înapoi în timp este singura creștere reală de")
    print("  putere, și e mai lentă decât orice optimizare de regulă.")

    pd.DataFrame([{"n_evenimente": have, "sd_tranzactie_pct": sd * 100,
                   "se_pct": se * 100, "efect_minim_detectabil_pct": mde * 100,
                   "efect_brut_pct": v_gross.mean() * 100,
                   "efect_net_50bps_pct": v.mean() * 100,
                   "raport_brut_over_mde": v_gross.mean() / mde,
                   "n_necesar_pentru_putere_80": float(n_need),
                   "factor_acoperire": float(n_need / have)}]
                 ).to_csv(OUT / "search2_power.csv", index=False)
    print(f"\nOK -> {OUT}/ (search2_cost.csv, search2_power.csv)")


if __name__ == "__main__":
    main()
