"""fetch_bvb.py — descarca zilnice BVB (indici + blue-chips) 2020-2026 via wapi.bvb.ro.
ponytail: stdlib+requests+pandas doar; cache local, retry la 401 tranzient.
Utilizare: python fetch_bvb.py [--from 2020-01-01] [--to 2026-09-28]

ATENTIE LA DIVIDENDE: parametrul ajust=1 al feed-ului ajusteaza DOAR spliturile, NU
dividendele — verificat empiric (TLV 11.06.2024: -4.69% identic in seria ajustata si
neajustata). Prin urmare randamentele de pret din aceasta serie sunt contaminate in
ferestrele de ex-dividend (sezonul iunie la bancile romanesti). BET-TR este indicele de
randament total al BVB si este imune; analyze.py il foloseste ca seria primara si
flagheaza automat orice eveniment contaminat (vezi contaminat_dividend).
Ceil: upgrade = serii oficiale de total return pe actiuni individuale (inexistente public).
"""
import argparse, time, sys, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import requests
import pandas as pd

BASE = "https://wapi.bvb.ro"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; bvb-go)",
           "Referer": "https://www.bvb.ro/"}
TICKERS = ["BET", "TLV", "SNP", "BRD", "H2O", "SNG", "DIGI", "TEL", "SNN",
           "ROTX", "BET-TR", "BET-FI", "BET-NG"]
# indicele folosit pentru inferenta principala: randament total, imune la ex-dividend
PRIMARY_INDEX = "BET-TR"
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

def fetch_hist(sess, symbol, frm, to, rs="1D", retries=4):
    span_days = max(1, (to - frm).days + 1)
    countback = str(min(span_days + 10, 5000))
    q = urllib.parse.urlencode({"symbol": symbol, "from": int(frm.timestamp()),
        "to": int(to.timestamp()), "rs": rs, "ajust": "1",
        "countback": countback, "currencyCode": "RON"})
    url = f"{BASE}/api/history?{q}"
    for i in range(retries):
        r = sess.get(url, timeout=30)
        if r.status_code == 200:
            j = r.json()
            if j.get("s") == "no_data":
                return []
            if j.get("s") != "ok":
                raise RuntimeError(f"{symbol}: status {j.get('s')}")
            n = len(j["t"])
            out = []
            for k in range(n):
                d = datetime.fromtimestamp(j['t'][k], tz=timezone.utc).date().isoformat()
                if d < frm.date().isoformat() or d > to.date().isoformat():
                    continue  # datafeed intoarce ultimele N bare pana la `to`, taie la range cerut
                vv = j.get("v", [])[k] if k < len(j.get("v", [])) else 0
                out.append({"date": d,
                     "ticker": symbol, "open": j["o"][k], "high": j["h"][k],
                     "low": j["l"][k], "close": j["c"][k],
                     "volume": int(vv or 0)})
            return out
        if r.status_code in (401, 429, 500, 502, 503):
            time.sleep(2 + i * 2)  # ponytail: gating tranzient BVB, backoff simplu
            continue
        raise RuntimeError(f"{symbol}: HTTP {r.status_code} {r.text[:200]}")
    raise RuntimeError(f"{symbol}: esec dupa {retries} incercari (gating BVB)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", default="2024-01-01")
    ap.add_argument("--to", dest="to", default="2026-09-28")
    a = ap.parse_args()
    frm = datetime.fromisoformat(a.frm).replace(tzinfo=timezone.utc)
    to = datetime.fromisoformat(a.to).replace(tzinfo=timezone.utc)
    sess = requests.Session(); sess.headers.update(HEADERS)
    allbars = []
    for t in TICKERS:
        print(f"fetch {t} ...", flush=True)
        try:
            bars = fetch_hist(sess, t, frm, to)
        except Exception as e:
            print(f"  EROARE {t}: {e}", file=sys.stderr)
            continue
        print(f"  {len(bars)} bare")
        allbars += bars
        time.sleep(1.2)  # spatiere anti-gating
    if not allbars:
        sys.exit("nimic descarcat — verifica reteaua/BVB")
    df = pd.DataFrame(allbars).sort_values(["ticker", "date"])
    df.to_csv(DATA / "prices_daily.csv", index=False)
    print(f"OK -> {DATA/'prices_daily.csv'} ({len(df)} randuri, {df.ticker.nunique()} simboluri)")

if __name__ == "__main__":
    main()
