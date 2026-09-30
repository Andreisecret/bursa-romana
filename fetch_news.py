import re
from pathlib import Path
from datetime import datetime, timezone
import requests
import feedparser

FEEDS = {
    "g4media": "https://www.g4media.ro/feed",
    "hotnews": "https://hotnews.ro/feed",
    "digi24": "https://www.digi24.ro/rss",
    "economica": "https://www.economica.net/feed",
}
KEYWORDS = ["alegeri", "preziden", "parlamentare", "ccr", "curtea constitu",
    "guvern", "motiune", "demisie", "ciolacu", "simion", "georgescu",
    "lasconi", "nicusor", "anton", "bec", "turul", "vot", "bolojan",
    "parlament", "coalitie", "bursa", "bet", "fitch", "moody"]
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}

def main():
    import pandas as pd
    raws, pols = [], []
    sess = requests.Session(); sess.headers.update(UA)
    for src, url in FEEDS.items():
        try:
            content = sess.get(url, timeout=20).content
        except Exception as e:
            print(f"{src}: EROARE {e}")
            continue
        feed = feedparser.parse(content)
        print(f"{src}: {len(feed.entries)} intrari")
        for e in feed.entries:
            title = (e.get("title") or "").strip()
            link = (e.get("link") or "").strip()
            pub = e.get("published") or e.get("updated") or ""
            low = f"{title} {e.get('summary','')}".lower()
            row = {"sursa": src, "titlu": title, "link": link,
                   "published": pub, "colectat_la": datetime.now(timezone.utc).isoformat()}
            raws.append(row)
            if any(k in low for k in KEYWORDS):
                pols.append(row)
    df = pd.DataFrame(raws).drop_duplicates(subset="link")
    df.to_csv(DATA / "news_raw.csv", index=False)
    dp = pd.DataFrame(pols).drop_duplicates(subset="link")
    dp.to_csv(DATA / "news_politic.csv", index=False)
    print(f"OK -> news_raw.csv ({len(df)}), news_politic.csv ({len(dp)})")
    print("NOTA: RSS acopera doar prezentul; istoricul 2024-2026 sta in events.csv.")

if __name__ == "__main__":
    main()
