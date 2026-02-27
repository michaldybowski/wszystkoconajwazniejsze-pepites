import re
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator

SOURCE_URL = "https://wszystkoconajwazniejsze.pl/pepites/"
FEED_TITLE = "WszystkoCoNajważniejsze – Pepites (wrapper)"
FEED_LINK = SOURCE_URL
MAX_ITEMS = 30

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def main():
    html = requests.get(SOURCE_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "lxml")

    # Na stronie /pepites/ wpisy są prezentowane jako nagłówki H2 z linkami do artykułów
    # (widać to w treści HTML: "## [tytuł]" + link). :contentReference[oaicite:2]{index=2}
    links = []
    for h2 in soup.select("h2"):
        a = h2.find("a", href=True)
        if not a:
            continue
        title = clean(a.get_text())
        url = a["href"].strip()
        if not title or not url.startswith("http"):
            continue

        # Spróbuj pobrać krótki opis z najbliższego tekstu po H2 (często jest to lead)
        desc = ""
        # znajdź następny element tekstowy (np. <p> lub zwykły tekst)
        nxt = h2.find_next()
        if nxt and nxt.name in ("p", "div"):
            desc = clean(nxt.get_text())
        links.append((title, url, desc))

    # Deduplikacja po URL
    seen = set()
    items = []
    for t, u, d in links:
        if u in seen:
            continue
        seen.add(u)
        items.append((t, u, d))
        if len(items) >= MAX_ITEMS:
            break

fg = FeedGenerator()
fg.id(FEED_LINK)
fg.title(FEED_TITLE)
fg.description("Automatycznie generowany RSS na podstawie listingu /pepites/ w serwisie WszystkoCoNajważniejsze.")
fg.link(href=FEED_LINK, rel="alternate")
SELF_URL = os.getenv("FEED_SELF_URL", "rss.xml")
fg.link(href=SELF_URL, rel="self")fg.language("pl")
fg.updated(datetime.now(timezone.utc))

    for title, url, desc in items:
        fe = fg.add_entry()
        fe.id(url)
        fe.title(title)
        fe.link(href=url)
        if desc:
            fe.description(desc)
        fe.updated(datetime.now(timezone.utc))

    fg.rss_file("rss.xml")

if __name__ == "__main__":
    main()
