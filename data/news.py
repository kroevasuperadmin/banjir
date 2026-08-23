"""Google News RSS search for banjir (flood) stories by Malaysian state.

Publisher: Google News (rss feeds of local news outlets)
Uses only stdlib (no feedparser) and respects a 5-min cache + 10s timeout.
"""
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

TTL = 300
TIMEOUT = 10

_FEED_URL = "https://news.google.com/rss/search?q={q}&hl={hl}&gl=MY&ceid=MY:{hl}"

_cache = {}


def _parse_date(s):
    if not s:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(s, fmt).isoformat()
        except ValueError:
            pass
    return s


def _publisher(item):
    """Try the <source> tag first, then a crude domain fallback."""
    source = item.find("source")
    if source is not None and source.text:
        return source.text.strip()
    link = item.findtext("link") or ""
    m = re.search(r"https?://(?:www\.)?([^/]+)", link)
    return m.group(1) if m else "news outlet"


def _title(item):
    return (item.findtext("title") or "").strip()


def _link(item):
    return (item.findtext("link") or "").strip()


def _fetch(q, hl="ms"):
    url = _FEED_URL.format(q=urllib.parse.quote(q), hl=hl)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def news(state_name, query="banjir"):
    """Return up to 5 news items for `state_name + query`. Falls back to national query."""
    q = f"{query} {state_name or ''}".strip()
    key = q
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]

    xml_text = _fetch(q, hl="ms") or _fetch(q, hl="en")
    if not xml_text:
        _cache[key] = (time.time(), [])
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        _cache[key] = (time.time(), [])
        return []

    channel = root.find("channel")
    if channel is None:
        _cache[key] = (time.time(), [])
        return []

    items = []
    for item in channel.findall("item")[:5]:
        title = _title(item)
        if not title:
            continue
        items.append({
            "title": title,
            "publisher": _publisher(item),
            "published": _parse_date(item.findtext("pubDate")),
            "url": _link(item),
        })

    _cache[key] = (time.time(), items)
    return items


if __name__ == "__main__":
    import json
    print(json.dumps(news("Selangor"), ensure_ascii=False, indent=1))
