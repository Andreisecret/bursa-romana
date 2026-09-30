import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import requests


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from analyze import load_prices, PRIMARY
from fetch_news import FEEDS, KEYWORDS
import feedparser

HERE = ROOT / "monitor"
OUT = HERE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
REGISTER = HERE / "register.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}


def thresholds():
    px, _ = load_prices()
    r = px[PRIMARY].pct_change().dropna() * 100
    a = r.abs()
    return {q: float(np.percentile(a, q)) for q in (90, 95, 99)}, px


def recent_political_news(hours=36):


    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    hits = []
    sess = requests.Session(); sess.headers.update(UA)
    for src, url in FEEDS.items():
        try:
            feed = feedparser.parse(sess.get(url, timeout=20).content)
        except Exception as e:
            print(f"  [rss] {src}: {e}")
            continue
        for e in feed.entries:
            title = (e.get("title") or "").strip()
            if not any(k in title.lower() for k in KEYWORDS):
                continue
            pub = e.get("published_parsed") or e.get("updated_parsed")
            if pub:
                ts = datetime(*pub[:6], tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            hits.append({"sursa": src, "titlu": title,
                         "link": (e.get("link") or "").strip()})
    return hits


def detect(threshold):
    thr, px = thresholds()
    if threshold is None:
        threshold = thr[95]
    last = px[PRIMARY].dropna()
    r = last.pct_change() * 100
    today = last.index[-1]
    move = float(r.iloc[-1])
    print(f"ultima sedinta: {today.date()}   BET-TR {last.iloc[-1]:.2f}   "
          f"randament {move:+.2f}%")
    print(f"prag p95 {thr[95]:.2f}%  p99 {thr[99]:.2f}%  |  prag folosit {threshold:.2f}%")

    if abs(move) < threshold:
        print("nicio sedinta peste prag. Nimic de inregistrat.")
        print("Asta e un rezultat, nu o eroare: majoritatea zilelor nu sunt socuri.")
        return None

    print(f"\nSOC DETECTAT: {move:+.2f}% (|moves| peste prag)")
    news = recent_political_news()
    print(f"articole politice in ultimele 36h: {len(news)}")
    for n in news[:8]:
        print(f"  - [{n['sursa']}] {n['titlu']}")
    if not news:
        print("  (niciun articol politic gasit -> soc fara cauza politica evidenta)")


    rec = OUT / "recovery_events.csv"
    if rec.exists():
        d = pd.read_csv(rec)
        band = d[(d.move_pct <= 0) &
                 (d.move_pct.abs() >= abs(move) * 0.6) &
                 (d.move_pct.abs() <= abs(move) * 1.6)]
        if len(band) == 0:
            band = d[(d.move_pct <= 0) & (d.move_pct.abs() >= 1.0)]
        if len(band):
            print(f"\nISTORIC, socuri de adancime comparabila (n={len(band)}):")
            for _, r_ in band.iterrows():
                print(f"  {r_['event_id']:24s} {r_['move_pct']:+6.2f}%  "
                      f"refacut in {r_['days_to_recover']} sedinte "
                      f"(retr_20 {r_['retr_20']:+.0f}%)")
            med = band.days_to_recover.median()
            print(f"  mediana: {med:.0f} sedinte pana la refacere")
            print("  ATENTIE: din monitor/recovery.py, caderile fara stire politica")
            print("  se refac la fel sau mai repede. Refacerea NU e semnal de cumparat.")

    row = {
        "data_soc": today.date().isoformat(),
        "randament_pct": round(move, 2),
        "prag_pct": round(threshold, 2),
        "n_stiri_politice_36h": len(news),
        "titluri": " | ".join(n["titlu"] for n in news[:6]),
        "zile_pana_la_refacere": "", "refacat": "", "notat": "",
    }
    reg = pd.read_csv(REGISTER) if REGISTER.exists() else pd.DataFrame()
    if len(reg) and (reg.data_soc == row["data_soc"]).any():
        print(f"\n{row['data_soc']} e deja in registru. Nu scriu dublu.")
        return None
    reg = pd.concat([reg, pd.DataFrame([row])], ignore_index=True)
    reg.to_csv(REGISTER, index=False, encoding="utf-8")
    print(f"\nscrisa in {REGISTER.name}. Campurile de refacere raman goale pana la --resolve.")
    return row


def resolve():
    if not REGISTER.exists():
        print("registru inexistent. Ruleaza mai intai detect.")
        return


    reg = pd.read_csv(REGISTER, dtype=str).fillna("")
    px, _ = load_prices()
    last = px[PRIMARY].dropna()
    changed = 0
    for i, row in reg.iterrows():
        if str(row.get("zile_pana_la_refacere", "")).strip():
            continue
        d = pd.Timestamp(row.data_soc)
        if d not in last.index:
            print(f"{row.data_soc}: sedinta nu este in date, sarit")
            continue
        p = last.index.get_loc(d)
        remaining = len(last) - 1 - p
        if remaining < 60:

            print(f"{row.data_soc}: doar {remaining} sedinte dupa soc, "
                  f"rezultatul nu se poate stabili inca")
            continue
        pre = last.iloc[p - 1]
        fut = last.iloc[p:p + 61]
        above = fut[fut >= pre]
        reg.loc[i, "zile_pana_la_refacere"] = str(
            int(fut.index.get_loc(above.index[0])) if len(above) else -1)
        reg.loc[i, "refacat"] = "da" if len(above) else "nu"
        changed += 1
        print(f"{row.data_soc} ({row.randament_pct:+.2f}%): "
              f"{'refacut in ' + reg.loc[i, 'zile_pana_la_refacere'] + ' sedinte' if len(above) else 'NU s-a refacut in 60 sedinte'}")
    if changed:
        reg.to_csv(REGISTER, index=False, encoding="utf-8")
    print(f"\n{changed} linie/i completate. Registru: {REGISTER}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolve", action="store_true")
    ap.add_argument("--threshold", type=float, default=None)
    a = ap.parse_args()
    if a.resolve:
        resolve()
    else:
        detect(a.threshold)


if __name__ == "__main__":
    main()
