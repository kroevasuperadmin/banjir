"""JPS Public InfoBanjir scraper: live river levels + rainfall, all Malaysian states.

Publisher: Jabatan Pengairan dan Saliran (JPS) Malaysia, https://publicinfobanjir.water.gov.my
The site has no JSON API; we read the same HTML tables the public page renders.
Stdlib + requests only.
"""
import concurrent.futures
import datetime
import difflib
import html
import re
import time

import requests

BASE = "https://publicinfobanjir.water.gov.my"
WL_URL = BASE + "/aras-air/data-paras-air/aras-air-data/?state={code}&district=ALL&station=ALL&lang=en"
RF_URL = BASE + "/wp-content/themes/shapely/agency/searchresultrainfall.php?state={code}&district=ALL&station=ALL&loginStatus=0&language=1"
TIMEOUT = 10
TTL = 300  # seconds
STALE_H = 24  # a reading older than this is reported OFFLINE, not as a live level
HEADERS = {"User-Agent": "Mozilla/5.0 (Banjir hackathon flood-awareness agent)"}

# From the state <select> on /aras-air/data-paras-air/ (MCK = JPS mockup/test state, excluded).
STATES = {
    "PLS": "Perlis", "KDH": "Kedah", "PNG": "Pulau Pinang", "PRK": "Perak",
    "SEL": "Selangor", "WLH": "WP Kuala Lumpur", "PTJ": "WP Putrajaya",
    "NSN": "Negeri Sembilan", "MLK": "Melaka", "JHR": "Johor", "PHG": "Pahang",
    "TRG": "Terengganu", "KEL": "Kelantan", "SRK": "Sarawak", "SAB": "Sabah",
    "WLP": "WP Labuan",
}
ALIASES = {"kl": "kuala lumpur", "pj": "petaling", "jb": "johor bahru", "kb": "kota bharu", "kk": "kota kinabalu"}
LEVELS = ["OFFLINE", "UNKNOWN", "NORMAL", "ALERT", "WARNING", "DANGER"]

_cache = {}  # key -> (timestamp, value)
LAST_ERRORS = {}  # state code -> error string from the last fetch_all()


def _cached(key, fn):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    val = fn()
    _cache[key] = (time.time(), val)
    return val


def _get(url):
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.text


def _rows(page):
    """Cell lists per table row. Site HTML is malformed (stray </tr>, missing <tr>), so split on the 'No' cell."""
    for chunk in re.split(r"<td data-th='No'>", page)[1:]:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", "<td>" + chunk, re.S)
        yield [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells]


def _num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None  # '-', '', 'N/A'
    return None if v <= -999 else v  # -9999 = JPS sentinel for no reading


def _iso(s):
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).isoformat()
        except ValueError:
            pass
    return None


def _stale(iso):
    if not iso:
        return True
    return (datetime.datetime.now() - datetime.datetime.fromisoformat(iso)).total_seconds() > STALE_H * 3600


def _status(level, alert, warning, danger, updated="9999-01-01T00:00:00"):
    if level is None or _stale(updated):
        return "OFFLINE"
    for name, th in (("DANGER", danger), ("WARNING", warning), ("ALERT", alert)):
        if th is not None and level >= th:
            return name
    return "NORMAL" if any(t is not None for t in (alert, warning, danger)) else "UNKNOWN"


def _parse_wl(page, code):
    out = []
    for c in _rows(page):
        if len(c) < 12:
            continue
        level, normal, alert, warning, danger = map(_num, c[7:12])
        updated = _iso(c[6])
        out.append({
            "state": code, "station_id": c[1], "name": c[2], "district": c[3],
            "basin": c[4], "sub_basin": c[5], "updated": updated,
            "level": level, "normal": normal, "alert": alert, "warning": warning, "danger": danger,
            "status": _status(level, alert, warning, danger, updated),
        })
    return out


def fetch_state(code):
    """River-level stations for one state code (see STATES). Cached 5 min."""
    code = code.upper()
    return _cached(("wl", code), lambda: _parse_wl(_get(WL_URL.format(code=code)), code))


def fetch_all():
    """All states. Unreachable states are skipped and recorded in LAST_ERRORS."""
    LAST_ERRORS.clear()
    out = []
    with concurrent.futures.ThreadPoolExecutor(8) as ex:  # ~21s sequential -> ~4s
        for code, fut in [(c, ex.submit(fetch_state, c)) for c in STATES]:
            try:
                out.extend(fut.result())
            except Exception as e:  # noqa: BLE001 - one bad state must not kill the national view
                LAST_ERRORS[code] = f"{type(e).__name__}: {e}"
    return out


def _parse_rf(page, code):
    days = re.findall(r"<th[^>]*>\s*(\d\d/\d\d/\d{4})\s*</th>", page)  # 6 previous-day columns
    out = []
    for c in _rows(page):
        if len(c) < 13:
            continue
        out.append({
            "state": code, "station_id": c[1], "name": c[2], "district": c[3], "updated": _iso(c[4]),
            "daily_mm": {d: _num(v) for d, v in zip(days, c[5:11])},
            "today_mm": _num(c[11]), "last_hour_mm": _num(c[12]),
        })
    return out


def fetch_rainfall(code):
    """Rainfall stations for one state: 6 past daily totals, today-since-midnight, last hour (mm). Cached 5 min."""
    code = code.upper()
    return _cached(("rf", code), lambda: _parse_rf(_get(RF_URL.format(code=code)), code))


def _norm(s):
    s = re.sub(r"\(.*?\)", " ", s.lower())  # 'Gombak (WPKL)' -> 'gombak'
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(ALIASES.get(w, w) for w in s.split())


def nearest(place, stations=None, limit=10):
    """Stations whose district or name fuzzy-matches `place`, best first. Uses fetch_all() if stations not given."""
    q = _norm(place)
    if not q:
        return []
    # Gazetteer first: towns/suburbs -> JPS district (JPS has no coordinates; see data/places.py).
    try:
        from places import resolve as _resolve
    except ImportError:  # imported as a package (data.jps)
        from .places import resolve as _resolve
    hit = _resolve(place)
    if hit:
        code, district, _ = hit
        pool = stations if stations is not None else fetch_all()
        exact = [s for s in pool if s["state"] == code and s["district"] == district]
        if exact:
            order = {"DANGER": 0, "WARNING": 1, "ALERT": 2, "NORMAL": 3}
            exact.sort(key=lambda s: order.get(s["status"], 9))
            return exact[:limit]
    scored = []
    for s in stations if stations is not None else fetch_all():
        best = 0.0
        for field in (s["district"], s["name"], STATES.get(s["state"], "")):
            f = _norm(field)
            if q == f or f"{q}" in f.split() or q in f:
                best = max(best, 1.0)
            else:
                best = max(best, difflib.SequenceMatcher(None, q, f).ratio())
        if best >= 0.6:
            scored.append((best, s))
    scored.sort(key=lambda x: (-x[0], -LEVELS.index(x[1].get("status", "UNKNOWN"))))
    return [s for _, s in scored[:limit]]


if __name__ == "__main__":
    # self-check on parser logic (fails loudly if thresholds/parsing break)
    assert _status(103.21, 103.10, 104.10, 104.80) == "ALERT"
    assert _status(None, 1, 2, 3) == "OFFLINE" and _status(1.0, None, None, None) == "UNKNOWN"
    assert _status(5.0, 1, 2, 3, "2026-04-20T03:15:00") == "OFFLINE"  # stale reading is not a live DANGER
    assert _num("-9999.0") is None and _num("-") is None and _num("0.5") == 0.5

    t0 = time.time()
    allst = fetch_all()
    print(f"JPS river levels, fetched {time.time() - t0:.1f}s, {len(allst)} stations, {len(STATES)} states")
    for code, name in STATES.items():
        rows = [s for s in allst if s["state"] == code]
        off = sum(s["status"] == "OFFLINE" for s in rows)
        unk = sum(s["status"] == "UNKNOWN" for s in rows)
        print(f"  {code} {name:<16} {len(rows):>4} stations  ({off} offline/stale, {unk} no thresholds)  {LAST_ERRORS.get(code, '')}")
    hot = [s for s in allst if s["status"] in ("ALERT", "WARNING", "DANGER")]
    print(f"\n>= ALERT nationally: {len(hot)}")
    for s in sorted(hot, key=lambda s: -LEVELS.index(s["status"])):
        print(f"  {s['status']:<7} {s['state']} {s['name']} [{s['district']}] {s['level']} m "
              f"(alert {s['alert']} / warn {s['warning']} / danger {s['danger']}) @ {s['updated']}")
    print("\nnearest('Gombak'):", [(s["name"], s["status"]) for s in nearest("Gombak", allst)[:5]])
    print("nearest('KL'):", [(s["name"], s["status"]) for s in nearest("KL", allst)[:5]])
    rf = fetch_rainfall("WLH")
    wet = [r for r in rf if (r["today_mm"] or 0) > 0]
    print(f"\nrainfall WLH: {len(rf)} stations, {len(wet)} with rain since midnight; sample:", rf[0] if rf else None)
