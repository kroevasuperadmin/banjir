"""JKM InfoBencana: live open flood/disaster relief centres (PPS = Pusat Pemindahan Sementara) + evacuee counts.

Publisher: Jabatan Kebajikan Masyarakat (JKM) Malaysia, https://infobencanajkmv2.jkm.gov.my/landing/
(NADMA's Portal Bencana links this as the official "Info Bencana dan Pusat Pemindahan" dashboard.)
Endpoint: GET /api/pusat-buka.php?a=<state_id>&b=<disaster_id>  (0 = all). Undocumented; same JSON the dashboard map loads.
NOTE: the OLD host infobencanajkm.jkm.gov.my is dead/blocked — use the v2 host.
Stdlib + requests only.
"""
import time

import requests

BASE = "https://infobencanajkmv2.jkm.gov.my"
URL = BASE + "/api/pusat-buka.php?a={state}&b=0"
FALLBACK_URL = BASE + "/landing/"
TIMEOUT = 10
TTL = 300
HEADERS = {"User-Agent": "Mozilla/5.0 (Banjir hackathon flood-awareness agent)", "Accept": "application/json"}

# From the state dropdown on /landing/ (index.php?a=N). 0 = all Malaysia.
STATES = {
    "johor": 1, "kedah": 2, "kelantan": 3, "melaka": 4, "negeri sembilan": 5, "pahang": 6,
    "pulau pinang": 7, "perak": 8, "perlis": 9, "selangor": 10, "terengganu": 11,
    "sabah": 12, "sarawak": 13, "kuala lumpur": 14, "labuan": 15, "putrajaya": 16,
}
ALIASES = {"kl": "kuala lumpur", "wp kuala lumpur": "kuala lumpur", "penang": "pulau pinang", "n9": "negeri sembilan", "malacca": "melaka"}

_cache = {}  # state_id -> (ts, result)


def open_pps(state=None):
    """Open relief centres right now. state: name ("Selangor", "kl") or None for all Malaysia.

    Returns {available, source, fetched_at, state, count, evacuees, families, centres:[...]}
    or {available: False, reason, fallback_url} when JKM is unreachable. Never raises.
    """
    key = (state or "").strip().lower()
    key = ALIASES.get(key, key)
    sid = STATES.get(key, 0) if key else 0
    if key and key not in STATES:
        return {"available": False, "reason": f"unknown state '{state}'", "fallback_url": FALLBACK_URL,
                "known_states": sorted(STATES)}

    hit = _cache.get(sid)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]

    url = URL.format(state=sid)
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        points = data.get("points") if isinstance(data, dict) else data  # JKM returns bare [] when a state has none open
        points = points or []
    except Exception as e:  # network, HTTP, JSON — all mean "no live data", never crash the agent
        return {"available": False, "reason": f"{type(e).__name__}: {e}", "fallback_url": FALLBACK_URL, "source_url": url}

    centres = [{
        "id": p.get("id"),
        "name": p.get("name"),
        "state": p.get("negeri"),
        "district": p.get("daerah"),
        "mukim": p.get("mukim"),
        "disaster": p.get("bencana"),            # BM: "Banjir", "Kebakaran", "Ribut", ...
        "evacuees": int(p.get("mangsa") or 0),
        "families": int(p.get("keluarga") or 0),
        "occupancy_pct": p.get("kapasiti"),      # JKM 'kapasiti' = % of centre capacity in use (139 = over capacity)
        "lat": p.get("latti"),
        "lon": p.get("longi"),
    } for p in points]
    centres.sort(key=lambda c: -c["evacuees"])

    out = {
        "available": True,
        "source": "JKM InfoBencana (Jabatan Kebajikan Masyarakat)",
        "source_url": url,
        "dashboard_url": FALLBACK_URL,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "state": key or "all",
        "count": len(centres),
        "evacuees": sum(c["evacuees"] for c in centres),
        "families": sum(c["families"] for c in centres),
        "flood_count": sum(1 for c in centres if "banjir" in (c["disaster"] or "").lower()),
        "centres": centres,
        "note": "Live JKM feed; no per-centre timestamp in this endpoint. Dashboard shows its own 'kemaskini pada' time.",
    }
    _cache[sid] = (time.time(), out)
    return out


def nearest_pps(lat, lon, limit=3):
    """Nearest open centres to a point (km, haversine). Same availability contract as open_pps()."""
    import math
    d = open_pps()
    if not d["available"]:
        return d
    def km(c):
        la1, lo1, la2, lo2 = map(math.radians, (lat, lon, c["lat"], c["lon"]))
        a = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
        return 2 * 6371 * math.asin(math.sqrt(a))
    near = [dict(c, distance_km=round(km(c), 1)) for c in d["centres"] if c["lat"] and c["lon"]]
    near.sort(key=lambda c: c["distance_km"])
    return dict(d, centres=near[:limit], count=len(near[:limit]))


if __name__ == "__main__":
    import json
    d = open_pps()
    assert "available" in d
    if d["available"]:
        assert d["count"] == len(d["centres"]) and d["evacuees"] == sum(c["evacuees"] for c in d["centres"])
        assert open_pps("kl")["state"] == "kuala lumpur"
    assert open_pps("Atlantis")["available"] is False
    print(json.dumps(d, indent=1, ensure_ascii=False)[:1500])
    print(json.dumps(nearest_pps(3.139, 101.687), ensure_ascii=False)[:600])
