"""MET Malaysia live weather via data.gov.my Realtime Weather API.

Publisher: MET Malaysia (Jabatan Meteorologi Malaysia) via https://api.data.gov.my/weather/
Docs: https://developer.data.gov.my/realtime-api/weather
Trailing slash on endpoints is REQUIRED. Forecast updates daily; warnings "when required".
RATE LIMIT: 4 requests/minute (429 after) -> every call is disk-cached in data/.met_cache.json
(warnings 5 min, forecast 60 min, location list 24 h); on 429 a stale cached copy is served.
Stdlib + requests only.
"""
import difflib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://api.data.gov.my/weather"
SOURCE = "MET Malaysia via data.gov.my"
MYT = timezone(timedelta(hours=8))
_TYPE_RANK = {"Ds": 0, "Tn": 1, "St": 2, "Dv": 3, "Rc": 4}  # prefer district on name ties
ALIASES = {"kl": "kuala lumpur", "pj": "petaling jaya", "jb": "johor bahru", "kk": "kota kinabalu", "penang": "pulau pinang"}

# BM -> EN, from the API docs value table
FORECAST_EN = {
    "berjerebu": "Hazy", "tiada hujan": "No rain", "hujan": "Rain",
    "hujan di beberapa tempat": "Scattered rain", "hujan di satu dua tempat": "Isolated rain",
    "hujan di satu dua tempat di kawasan pantai": "Isolated rain over coastal areas",
    "hujan di satu dua tempat di kawasan pedalaman": "Isolated rain over inland areas",
    "ribut petir": "Thunderstorms", "ribut petir di beberapa tempat": "Scattered thunderstorms",
    "ribut petir di beberapa tempat di kawasan pedalaman": "Scattered thunderstorms over inland areas",
    "ribut petir di satu dua tempat": "Isolated thunderstorms",
    "ribut petir di satu dua tempat di kawasan pantai": "Isolated thunderstorms over coastal areas",
    "ribut petir di satu dua tempat di kawasan pedalaman": "Isolated thunderstorms over inland areas",
}
WHEN_EN = {"pagi": "Morning", "malam": "Night", "petang": "Afternoon", "pagi dan petang": "Morning and Afternoon",
           "pagi dan malam": "Morning and Night", "petang dan malam": "Afternoon and Night",
           "sepanjang hari": "Throughout the day"}


_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".met_cache.json")
TTL = {"warning": 300, "forecast": 3600, "locations": 86400}


def _get(path, ttl=None, **params):
    """GET with disk cache. ponytail: one JSON file, rewritten per miss; fine for a single bot process."""
    key = f"{path}?{json.dumps(params, sort_keys=True)}"
    try:
        cache = json.load(open(_CACHE_FILE, encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    hit = cache.get(key)
    if hit and time.time() - hit["t"] < (ttl or TTL.get(path, 300)):
        return hit["data"]
    try:
        r = requests.get(f"{BASE}/{path}/", params=params, timeout=20)
        r.raise_for_status()
    except requests.RequestException:
        if hit:  # rate-limited / offline: serve stale rather than fail
            return hit["data"]
        raise
    cache[key] = {"t": time.time(), "data": r.json()}
    json.dump(cache, open(_CACHE_FILE, "w", encoding="utf-8"))
    return cache[key]["data"]


def _areas(text):
    """Best-effort parse of affected areas from warning text_en. Not an official field."""
    out = []
    for states in re.findall(r"states? of (.+?)(?: until| till|\.\s|$)", text or "", flags=re.I | re.S):
        for chunk in states.split(";"):
            state, _, districts = chunk.partition(":")
            state = state.strip(" ,")
            ds = [re.sub(r"\s*\(.*?\)", "", d).strip() for d in districts.split(",") if d.strip()]
            out += [f"{d} ({state})" for d in ds] or [state]
    out += [f"waters of {w.strip()}" for w in re.findall(r"waters of (.+?)(?: until| till|\.\s)", text or "", flags=re.I)]
    return list(dict.fromkeys(out))


def warnings(include_expired=False):
    """Active MET Malaysia warnings (thunderstorm, heavy rain, strong wind/rough seas). Excludes 'No Advisory'."""
    now = datetime.now(MYT).replace(tzinfo=None)
    out = []
    for w in _get("warning", sort="-valid_to"):
        wi = w.get("warning_issue") or {}
        if (wi.get("title_en") or "").strip().lower() == "no advisory":
            continue
        valid_to = w.get("valid_to")
        if not include_expired and valid_to and datetime.fromisoformat(valid_to) < now:
            continue
        out.append({
            "title_en": wi.get("title_en"), "title_bm": wi.get("title_bm"),
            "heading_en": w.get("heading_en"), "issued": wi.get("issued"),
            "valid_from": w.get("valid_from"), "valid_to": valid_to,
            "text_en": w.get("text_en"), "text_bm": w.get("text_bm"),
            "instruction_en": w.get("instruction_en"), "instruction_bm": w.get("instruction_bm"),
            "areas": _areas(w.get("text_en")),  # inferred from text, not official
            "source": SOURCE,
        })
    return out


def locations():
    """All forecast locations [(id, name)] — 443 as of 2026-08-23. Disk-cached 24 h."""
    rows = _get("forecast", ttl=TTL["locations"], include="location")
    return list(dict.fromkeys((r["location"]["location_id"], r["location"]["location_name"]) for r in rows))


def match_location(name):
    """Fuzzy-match a user string to (id, name, score). Districts win ties over towns/states."""
    q = name.strip().lower()
    q = ALIASES.get(q, q)
    best = None
    for lid, lname in locations():
        n = lname.lower()
        score = 1.0 if n == q or n == f"wp {q}" else difflib.SequenceMatcher(None, q, n).ratio()
        if q in n and score < 0.9:
            score = 0.9
        key = (score, -_TYPE_RANK.get(lid[:2], 9))
        if best is None or key > best[0]:
            best = (key, lid, lname, score)
    return (best[1], best[2], round(best[3], 2)) if best and best[3] >= 0.6 else None


def forecast(location_name):
    """7-day MET forecast for the nearest matching location, or None if no match."""
    m = match_location(location_name)
    if not m:
        return None
    lid, lname, score = m
    days = []
    for r in _get("forecast", contains=f"{lid}@location__location_id", sort="date"):
        days.append({
            "date": r["date"],
            "morning": r["morning_forecast"], "afternoon": r["afternoon_forecast"], "night": r["night_forecast"],
            "summary": r["summary_forecast"], "summary_when": r["summary_when"],
            "summary_en": FORECAST_EN.get((r["summary_forecast"] or "").lower(), r["summary_forecast"]),
            "summary_when_en": WHEN_EN.get((r["summary_when"] or "").lower(), r["summary_when"]),
            "min_temp": r["min_temp"], "max_temp": r["max_temp"],
        })
    return {"query": location_name, "location_id": lid, "location_name": lname, "match_score": score,
            "days": days, "source": SOURCE}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"# MET Malaysia — {datetime.now(MYT):%Y-%m-%d %H:%M} MYT — source: {SOURCE}\n")
    ws = warnings()
    print(f"## Active warnings: {len(ws)}")
    for w in ws:
        print(f"- {w['title_en']} / {w['title_bm']} | issued {w['issued']} | valid {w['valid_from']} -> {w['valid_to']}")
        print(f"  areas (parsed): {w['areas']}")
        print(f"  text: {(w['text_en'] or '')[:300].replace(chr(10), ' ')}")
    for q in sys.argv[1:] or ["Kuala Lumpur", "Gombak"]:
        f = forecast(q)
        print(f"\n## Forecast: {q} -> {f['location_name']} ({f['location_id']}, match {f['match_score']})" if f else f"\n## Forecast: {q} -> no match")
        for d in (f or {}).get("days", []):
            print(f"- {d['date']}: {d['summary']} ({d['summary_en']}, {d['summary_when_en']}) {d['min_temp']}-{d['max_temp']}C")
    assert match_location("kuala lumpur")[0] == "Ds058" and match_location("gombak")[0] == "Ds055"
    assert _areas("expected over the state of Sarawak: Sri Aman, Samarahan, Serian (Serian) until 12:00 PM") == \
        ["Sri Aman (Sarawak)", "Samarahan (Sarawak)", "Serian (Sarawak)"]
    assert match_location("zzzzzz") is None and match_location("KL")[0] == "Ds058"
