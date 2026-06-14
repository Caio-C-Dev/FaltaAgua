import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone

from config import QUERIES_GOOGLE_NEWS


def _build_url(query: str) -> str:
    q = urllib.parse.quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def fetch_recent_news(hours: int = 3) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    seen_links = set()
    items = []

    for q in QUERIES_GOOGLE_NEWS:
        feed = feedparser.parse(_build_url(q))
        for entry in feed.entries:
            link = entry.get("link", "")
            if link in seen_links:
                continue
            seen_links.add(link)

            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue

            items.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "link": link,
                "published": entry.get("published", ""),
            })

    return items
