"""fetch_intraday.py — extensia C: bare 15min BET+TLV in jurul socurilor majore.
Ferestre: tur1_2024 (22-27 nov 2024), tur1_2025 (30 apr-7 mai 2025), tur2_2025 (16-20 mai 2025).
Masoara: gap la open ziua socului, timp pana la minimul zilei, recuperare day+1.
Utilizare: python fetch_intraday.py -> data/intraday_15m.csv + outputs/fig_intraday_*.png
"""
import time, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "https://wapi.bvb.ro"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; bvb-go)", "Referer": "https://www.bvb.ro/"}
ROOT = Path(__file__).parent
DATA = ROOT / "data"; OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)
RO = ZoneInfo("Europe/Bucharest")
WINDOWS = {
    "tur1_2024": ("2024-11-22", "2024-11-27", "2024-11-25"),
    "tur1_2025": ("2025-04-30", "2025-05-07", "2025-05-05"),
    "tur2_2025": ("2025-05-16", "2025-05-20", "2025-05-19"),
}

def fetch(sess, symbol, frm, to, rs="15"):
    q = urllib.parse.urlencode({"symbol": symbol, "from": int(frm.timestamp()),
        "to": int(to.timestamp()), "rs": rs, "ajust": "1",
        "countback": "2000", "currencyCode": "RON"})
    for i in range(4):
        r = sess.get(f"{BASE}/api/history?{q}", timeout=30)
        if r.status_code == 200:
            j = r.json()
            if j.get("s") == "no_data":
                return []
            assert j.get("s") == "ok", j.get("s")
            return [{"ts_utc": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
                     "ts_ro": datetime.fromtimestamp(t, tz=timezone.utc).astimezone(RO).isoformat(),
                     "ticker": symbol, "close": c}
                    for t, c in zip(j["t"], j["c"])]
        time.sleep(2 + i * 2)
    raise RuntimeError(f"{symbol} esec intraday")

def main():
    sess = requests.Session(); sess.headers.update(HEADERS)
    allbars = []
    for name, (f, t, _) in WINDOWS.items():
        frm = datetime.fromisoformat(f).replace(tzinfo=timezone.utc)
        to = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        for sym in ["BET", "TLV"]:
            print(f"fetch {sym} {name} ...", flush=True)
            allbars += [{"window": name, **b} for b in fetch(sess, sym, frm, to)]
            time.sleep(1.2)
    df = pd.DataFrame(allbars)
    df["ts_ro"] = pd.to_datetime(df["ts_ro"], utc=True).dt.tz_convert(RO)
    # datafeed intoarce ultimele 2000 bare pana la `to`; taie la fereastra ceruta
    bounds = {n: (pd.Timestamp(f, tz=timezone.utc) - pd.Timedelta(days=7), pd.Timestamp(t, tz=timezone.utc) + pd.Timedelta(days=1)) for n, (f, t, _) in WINDOWS.items()}
    df = df[df.apply(lambda r: bounds[r["window"]][0] <= r["ts_ro"] <= bounds[r["window"]][1], axis=1)]
    df.to_csv(DATA / "intraday_15m.csv", index=False)
    print(f"OK -> intraday_15m.csv ({len(df)} bare)")

    for name, (_, _, shock) in WINDOWS.items():
        sub = df[df.window == name]
        fig, ax = plt.subplots(figsize=(11, 4.5))
        for sym in ["BET", "TLV"]:
            s = sub[sub.ticker == sym].sort_values("ts_ro")
            base = s[s.ts_ro.dt.date.astype(str) < shock]["close"].iloc[-1] if any(s.ts_ro.dt.date.astype(str) < shock) else s["close"].iloc[0]
            ax.plot(s["ts_ro"], (s["close"] / base - 1) * 100, lw=1.3, label=f"{sym} (rebazat pre-soc)")
        ax.axvline(pd.Timestamp(shock, tz=RO), color="r", ls="--", lw=1, label=f"ziua socului {shock}")
        ax.set_ylabel("% cumulativ vs inchiderea pre-soc")
        ax.set_title(f"{name}: viteza reactiei intraday (15min)")
        ax.legend(fontsize=8); fig.autofmt_xdate(); fig.tight_layout()
        fig.savefig(OUT / f"fig_intraday_{name}.png", dpi=130)
    # viteza: gap open + minim ziua socului (BET)
    for name, (_, _, shock) in WINDOWS.items():
        s = df[(df.window == name) & (df.ticker == "BET")].sort_values("ts_ro")
        pre = s[s.ts_ro.dt.date.astype(str) < shock]["close"].iloc[-1]
        d0 = s[s.ts_ro.dt.date.astype(str) == shock]
        if len(d0):
            gap = (d0["close"].iloc[0] / pre - 1) * 100
            mn = (d0["close"].min() / pre - 1) * 100
            tmin = d0.loc[d0["close"].idxmin(), "ts_ro"]
            print(f"{name}: gap-open {gap:+.2f}% | minim zi {mn:+.2f}% la {tmin} | inchidere {(d0['close'].iloc[-1]/pre-1)*100:+.2f}%")

if __name__ == "__main__":
    main()
