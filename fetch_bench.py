import time
from datetime import datetime, timezone
from pathlib import Path
import requests
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}

def fetch_range(sess, p1, p2):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/%5ESTOXX"
           f"?interval=1d&period1={int(p1.timestamp())}&period2={int(p2.timestamp())}")
    r = sess.get(url, timeout=30)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    return [(datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat(), c)
            for t, c in zip(ts, closes) if c]

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", default="2020-01-01")
    a = ap.parse_args()
    sess = requests.Session(); sess.headers.update(UA)
    p1 = datetime.fromisoformat(a.frm).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    rows = []
    cur = p1
    while cur < now:
        nxt = min(datetime(cur.year + 1, 1, 1, tzinfo=timezone.utc), now)
        rows += fetch_range(sess, cur, nxt)
        cur = nxt
        time.sleep(0.5)
    df = pd.DataFrame(rows, columns=["date", "stoxx_close"]).drop_duplicates("date").sort_values("date")
    df.to_csv(DATA / "bench_daily.csv", index=False)
    print(f"OK -> bench_daily.csv ({len(df)} zile)")

if __name__ == "__main__":
    main()
