# -*- coding: utf-8 -*-
"""Banjir API - FastAPI entrypoint. Serves web/index.html and /api/{status,pitch,health}."""
import concurrent.futures
import difflib
import json
import os
import re
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Make repo root importable from this package both locally and on Vercel
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data import emergency, jps, met, places, pps

MYT = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# Cache / persistence helpers
# ---------------------------------------------------------------------------
TMP = tempfile.gettempdir()
JPS_CACHE_FILE = os.environ.get("BANJIR_JPS_CACHE", os.path.join(TMP, "banjir_jps_cache.json"))
MET_CACHE_FILE = os.environ.get("BANJIR_MET_CACHE", os.path.join(TMP, "banjir_met_cache.json"))

# MET disk cache lives in /tmp on Vercel (writable) instead of the source tree
met._CACHE_FILE = MET_CACHE_FILE


def _now():
    return datetime.now(MYT)


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def _jps_fetch_all():
    """Wrap JPS national fetch with a disk fallback for the 'JPS site down' edge case."""
    try:
        stations = jps.fetch_all()
    except Exception as e:
        stations = []
        jps.LAST_ERRORS["network"] = str(e)

    errors = dict(jps.LAST_ERRORS)
    if stations:
        _save_json(JPS_CACHE_FILE, {
            "t": time.time(),
            "stations": stations,
            "errors": errors,
        })
        return stations, errors, False

    # nothing live - try last good disk cache
    cached = _load_json(JPS_CACHE_FILE)
    if cached and time.time() - cached.get("t", 0) < jps.TTL:
        return cached["stations"], cached.get("errors", {}), True
    return [], errors, False


def _jps_fetch_state(code):
    """Fetch one state's stations only. Falls back to the national disk cache if JPS is down."""
    code = code.upper()
    try:
        stations = jps.fetch_state(code)
        return stations, {}, False
    except Exception as e:
        errors = {code: f"{type(e).__name__}: {e}"}
        cached = _load_json(JPS_CACHE_FILE)
        if cached and time.time() - cached.get("t", 0) < jps.TTL:
            state_stations = [s for s in cached["stations"] if s.get("state") == code]
            return state_stations, errors, True
        return [], errors, False


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Banjir API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_INDEX = ROOT / "web" / "index.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    return HTMLResponse(WEB_INDEX.read_text(encoding="utf-8"))


@app.get("/api/health")
def health():
    return {"ok": True, "time": _now().isoformat()}


# ---------------------------------------------------------------------------
# Place / state resolution
# ---------------------------------------------------------------------------
def _state_name(code):
    return jps.STATES.get(code, code)


def _resolve_state(place, stations):
    """Return (state_code, state_name, source) from the best station or place text."""
    if stations:
        code = stations[0]["state"]
        return code, _state_name(code), "station"

    q = jps._norm(place)
    if not q:
        return None, None, None

    # aliases
    if q in jps.ALIASES:
        q = jps.ALIASES[q]

    scored = []
    for code, name in jps.STATES.items():
        n = jps._norm(name)
        score = difflib.SequenceMatcher(None, q, n).ratio()
        if q == n or q in n.split() or n in q.split():
            score = max(score, 0.95)
        if score >= 0.5:
            scored.append((score, code, name))
    if not scored:
        return None, None, None
    scored.sort(key=lambda x: -x[0])
    return scored[0][1], scored[0][2], "place"


def _suggest(place, stations):
    """When no river station matches, suggest nearby districts or states."""
    q = jps._norm(place)
    if not q:
        return []
    # Start with a few known high-profile districts so an empty query still gets examples
    known = ["gombak", "kuala lumpur", "kota bharu", "petaling jaya", "johor bahru", "george town", "kuching", "kota kinabalu"]
    targets = list({jps._norm(s["district"]) for s in stations}) + \
              [jps._norm(n) for n in jps.STATES.values()]
    targets = list(set(targets))
    matches = difflib.get_close_matches(q, targets, n=8, cutoff=0.7)
    # if the query doesn't look like any Malaysian district/state, show the 8 common examples
    return matches if matches else known


# ---------------------------------------------------------------------------
# Trend / rainfall hint
# ---------------------------------------------------------------------------
def _attach_trend(stations, state_code):
    if not state_code or not stations:
        return
    try:
        rf = jps.fetch_rainfall(state_code)
    except Exception:
        return
    # district -> max last_hour/today
    by_district = {}
    for r in rf:
        d = jps._norm(r.get("district", ""))
        by_district.setdefault(d, {"last_hour": 0.0, "today": 0.0})
        by_district[d]["last_hour"] = max(by_district[d]["last_hour"], r.get("last_hour_mm") or 0)
        by_district[d]["today"] = max(by_district[d]["today"], r.get("today_mm") or 0)
    for s in stations:
        d = jps._norm(s.get("district", ""))
        rain = by_district.get(d, {"last_hour": 0.0, "today": 0.0})
        s["rain_last_hour_mm"] = rain["last_hour"]
        s["rain_today_mm"] = rain["today"]
        if rain["last_hour"] > 0:
            s["trend"] = "rising with rain in the last hour"
        elif rain["today"] > 0:
            s["trend"] = "rain today; watch closely"
        else:
            s["trend"] = "steady - no rain nearby"


# ---------------------------------------------------------------------------
# Warnings, forecast, relief, emergency
# ---------------------------------------------------------------------------
def _filter_warnings(warnings, state_name, place):
    """Return MET warnings that mention the resolved state/area."""
    if not state_name:
        return warnings[:5]
    state_key = state_name.lower()
    matched = []
    for w in warnings:
        text = " ".join([w.get("title_en") or "", w.get("title_bm") or "",
                         w.get("text_en") or "", w.get("text_bm") or ""]).lower()
        areas = [a.lower() for a in w.get("areas", [])]
        if state_key in text or any(state_key in a for a in areas):
            matched.append(w)
    return matched if matched else warnings[:5]


def _next_24h(forecast):
    if not forecast or not forecast.get("days"):
        return None
    today = forecast["days"][0]
    return {
        "date": today["date"],
        "summary_bm": today["summary"],
        "summary_en": today["summary_en"],
        "when_bm": today["summary_when"],
        "when_en": today["summary_when_en"],
        "min_temp": today["min_temp"],
        "max_temp": today["max_temp"],
        "location": forecast.get("location_name"),
        "match_score": forecast.get("match_score"),
        "source": "MET Malaysia via data.gov.my",
    }


def _relief(state_name, place):
    """Return relief centres for the state, honest fallback if JKM is down."""
    d = pps.open_pps(state_name.lower() if state_name else None)
    if not d.get("available"):
        return {
            "available": False,
            "reason": d.get("reason", "JKM InfoBencana unavailable"),
            "dashboard_url": d.get("dashboard_url", "https://infobencanajkmv2.jkm.gov.my/landing/"),
            "source": "JKM InfoBencana",
        }
    centres = d.get("centres", [])
    # prefer flood-specific, then any
    flood = [c for c in centres if "banjir" in (c.get("disaster") or "").lower()]
    top = (flood or centres)[:3]
    return {
        "available": True,
        "count": d.get("count"),
        "flood_count": d.get("flood_count"),
        "evacuees": d.get("evacuees"),
        "fetched_at": d.get("fetched_at"),
        "source": d.get("source"),
        "dashboard_url": d.get("dashboard_url"),
        "centres": top,
    }


# ---------------------------------------------------------------------------
# Risk + explanation + pitch
# ---------------------------------------------------------------------------
RISK_ORDER = {"DANGER": 4, "WARNING": 3, "ALERT": 2, "NORMAL": 1, "UNKNOWN": 0, "OFFLINE": -1}
RISK_COLOR = {"DANGER": "red", "WARNING": "orange", "ALERT": "amber", "NORMAL": "green", "UNKNOWN": "gray", "OFFLINE": "gray"}


def _top_risk(stations):
    if not stations:
        return None
    best = max(stations, key=lambda s: RISK_ORDER.get(s.get("status"), -1))
    return best.get("status")


def _build_explanation(place, stations, risk, forecast, warnings, relief):
    """Deterministic BM/EN summary. Demo works even when Qwen key is missing."""
    if not stations:
        return {
            "bm": f"Maaf, kami tidak pasti di mana {place}. Cuba taip nama bandar/kawasan yang hampir.",
            "en": f"Sorry, we couldn't locate {place}. Try a nearby town or district.",
            "risk_level": None,
            "risk_color": "gray",
        }

    top = stations[0]
    level_text = "no reading" if top.get("level") is None else f"{top['level']} m"
    status = top.get("status")
    trend = top.get("trend", "")
    warn_count = len(warnings or [])
    forecast_text = forecast.get("summary_bm") if forecast else "no forecast"
    forecast_en = forecast.get("summary_en") if forecast else "no forecast"

    if status in ("DANGER", "WARNING"):
        bm = (f"Paras air terhampir {place} di {top['name']} ({top['district']}) adalah {level_text} - {status}. "
              f"Arahan: berpindah segera jika diarahkan. Terdapat {warn_count} amaran MET aktif. "
              f"Ramalan: {forecast_text}.")
        en = (f"The nearest river level to {place} at {top['name']} ({top['district']}) is {level_text} - {status}. "
              f"Action: evacuate immediately if told. There are {warn_count} active MET warnings. "
              f"Forecast: {forecast_en}.")
    elif status == "ALERT":
        bm = (f"Paras air di {top['name']} ({top['district']}) mencecah ambang {status.lower()}: {level_text}. "
              f"Arahan: peka, sediakan beg kecemasan, pantau maklumat terkini. Trend: {trend}. "
              f"Ramalan 24 jam: {forecast_text}.")
        en = (f"The river level at {top['name']} ({top['district']}) has hit the {status} threshold: {level_text}. "
              f"Action: stay alert, prepare an emergency bag, watch for updates. Trend: {trend}. "
              f"24h forecast: {forecast_en}.")
    elif status == "NORMAL":
        bm = (f"Paras air di {top['name']} ({top['district']}) berada di paras normal ({level_text}). "
              f"Trend: {trend}. Ramalan 24 jam: {forecast_text}. Terus peka kepada amaran banjir.")
        en = (f"The river level at {top['name']} ({top['district']}) is normal ({level_text}). "
              f"Trend: {trend}. 24h forecast: {forecast_en}. Stay alert for flood warnings.")
    else:
        bm = (f"Stesen terhampir {place}, {top['name']}, tiada bacaan terkini atau ambang tidak tersedia. "
              f"Trend: {trend}. Ramalan 24 jam: {forecast_text}.")
        en = (f"The nearest station to {place}, {top['name']}, has no current reading or thresholds. "
              f"Trend: {trend}. 24h forecast: {forecast_en}.")

    return {"bm": bm, "en": en, "risk_level": status, "risk_color": RISK_COLOR.get(status, "gray")}


def _qwen_call(prompt, fallback_dict):
    """Call Qwen if configured; otherwise return the deterministic fallback."""
    key = os.environ.get("QWEN_API_KEY")
    base = os.environ.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    model = os.environ.get("QWEN_MODEL", "qwen3.8-max")
    if not key:
        return dict(fallback_dict, fallback=True, model=None)

    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 400,
            },
            timeout=10,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        try:
            data = json.loads(text)
            if "bm" in data and "en" in data:
                return dict(data, fallback=False, model=model)
        except Exception:
            pass
        return {"bm": text, "en": text, "fallback": False, "model": model}
    except Exception as e:
        return dict(fallback_dict, fallback=True, model=model, error=str(e))


def _qwen_explanation(place, data, fallback):
    prompt = (
        "You are Banjir, a calm Malaysian flood-awareness agent. "
        "Write a 2-sentence update in Bahasa Malaysia and a 2-sentence update in English. "
        "Return only JSON with keys 'bm' and 'en'.\n\nData:\n" + json.dumps(data, ensure_ascii=False)
    )
    return _qwen_call(prompt, fallback)


def _qwen_pitch(place, data, fallback):
    prompt = (
        "You are Banjir, pitching a 30-second Malaysian flood-awareness agent demo. "
        "Use the live data below and deliver it confidently in Bahasa Malaysia and English. "
        "Return only JSON with keys 'bm' and 'en'.\n\nData:\n" + json.dumps(data, ensure_ascii=False)
    )
    return _qwen_call(prompt, fallback)


# ---------------------------------------------------------------------------
# Status data (used by both /api/status and /api/pitch)
# ---------------------------------------------------------------------------
def _status_data(place: str):
    t0 = time.time()
    place = place.strip()

    # 1. resolve place: if the gazetteer gives a state, fetch only that state (~1s)
    resolved = places.resolve(place)
    if resolved:
        state_code, district, _ = resolved
        state_name = jps.STATES.get(state_code, state_code)
        state_source = "place"
    else:
        state_code, state_name, state_source = None, None, None

    # 2. parallel fetch JPS (slowest), MET warnings, MET forecast, JKM relief
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        if resolved:
            jps_future = ex.submit(_jps_fetch_state, state_code)
        else:
            jps_future = ex.submit(_jps_fetch_all)
        warnings_future = ex.submit(met.warnings)
        forecast_future = ex.submit(lambda p: met.forecast(p), place)
        relief_future = ex.submit(_relief, None, place)

    stations, jps_errors, used_cache = jps_future.result()
    warnings = warnings_future.result()
    forecast = forecast_future.result()
    relief = relief_future.result()

    nearest = jps.nearest(place, stations, limit=10)
    if not resolved:
        state_code, state_name, state_source = _resolve_state(place, nearest)

    # 3. if unknown place
    if not nearest:
        suggestions = _suggest(place, stations)
        return {
            "ok": False,
            "place": place,
            "place_not_found": True,
            "suggestions": suggestions,
            "message_bm": f"Kami tidak jumpa '{place}'. Cuba kawasan berikut:",
            "message_en": f"We couldn't find '{place}'. Try one of these nearby areas:",
            "generated_at": _now().isoformat(),
            "sources": [{
                "name": "JPS Malaysia",
                "url": "https://publicinfobanjir.water.gov.my",
                "status": "no station match",
            }],
        }

    # 3. attach trend using state rainfall
    _attach_trend(nearest, state_code)

    # 4. resolve a better forecast if place didn't match
    if not forecast:
        for candidate in [nearest[0].get("district"), state_name]:
            if candidate:
                forecast = met.forecast(candidate)
                if forecast:
                    break

    # 5. filter warnings + relief by resolved state
    warnings = _filter_warnings(warnings, state_name, place)
    relief = _relief(state_name, place)

    # 6. risk + emergency
    risk = _top_risk(nearest)
    hotlines = emergency.hotlines_for(state_name or "")
    checklist = emergency.checklist_for(risk)

    # 7. deterministic explanation (Qwen never blocks the response)
    fallback_explain = _build_explanation(place, nearest, risk, _next_24h(forecast), warnings, relief)
    explain = _qwen_explanation(place, {
        "place": place, "state": state_name, "top_station": nearest[0] if nearest else None,
        "warnings_count": len(warnings), "forecast": _next_24h(forecast),
    }, fallback_explain)

    # 8. source / freshness notes
    updated_times = [s.get("updated") for s in nearest if s.get("updated")]
    latest_station_update = max(updated_times) if updated_times else None
    jps_fresh = _now().isoformat()

    response = {
        "ok": True,
        "place": place,
        "resolved_state": state_name,
        "state_code": state_code,
        "generated_at": _now().isoformat(),
        "request_seconds": round(time.time() - t0, 2),
        "jps": {
            "source": "JPS Malaysia (publicinfobanjir)",
            "source_url": "https://publicinfobanjir.water.gov.my",
            "fetched_at": jps_fresh,
            "cached": used_cache,
            "last_errors": jps_errors,
            "station_count": len(stations),
            "latest_station_update": latest_station_update,
            "stations": nearest,
        },
        "met_warnings": warnings[:5],
        "met_forecast": _next_24h(forecast),
        "relief_centres": relief,
        "emergency": {
            "risk_level": risk,
            "risk_color": RISK_COLOR.get(risk, "gray"),
            "hotlines": hotlines,
            "checklist": checklist,
        },
        "explanation": explain,
        "sources": [
            {"name": "JPS Malaysia", "url": "https://publicinfobanjir.water.gov.my", "fetched_at": jps_fresh},
            {"name": "MET Malaysia", "url": "https://api.data.gov.my/weather", "fetched_at": _now().isoformat()},
            {"name": "JKM InfoBencana", "url": "https://infobencanajkmv2.jkm.gov.my/landing/", "fetched_at": relief.get("fetched_at")},
            {"name": "NADMA / APM hotlines", "url": "https://www.civildefence.gov.my/hotline-apm/", "fetched_at": _now().isoformat()},
        ],
    }
    return response


# ---------------------------------------------------------------------------
# /api/status
# ---------------------------------------------------------------------------
@app.get("/api/status")
def status(place: str = Query(..., min_length=1, description="Place name in Malaysia")):
    return JSONResponse(_status_data(place))


# ---------------------------------------------------------------------------
# /api/pitch
# ---------------------------------------------------------------------------
@app.get("/api/pitch")
def pitch(place: str = Query(..., min_length=1, description="Place name in Malaysia")):
    try:
        data = _status_data(place)
    except Exception as e:
        data = {"ok": False, "error": str(e)}

    fallback = {
        "bm": (f"Ini Banjir. Baru sahaja saya semak data sungai, amaran MET, ramalan, dan pusat pemindahan untuk {place}. "
               "Dapatkan status banjir terkini dalam Bahasa Malaysia dan English pada bila-bila masa."),
        "en": (f"This is Banjir. I just checked river levels, MET warnings, the forecast, and relief centres for {place}. "
               "Get live flood status in Bahasa Malaysia and English, anytime."),
    }

    pitch = _qwen_pitch(place, data, fallback)
    return JSONResponse({
        "ok": data.get("ok", False),
        "place": place,
        "pitch_bm": pitch.get("bm"),
        "pitch_en": pitch.get("en"),
        "fallback": pitch.get("fallback", True),
        "model": pitch.get("model"),
    })


# ---------------------------------------------------------------------------
# Local cache warmer (skip on Vercel serverless functions)
# ---------------------------------------------------------------------------
def _jps_warm():
    while True:
        try:
            _jps_fetch_all()
        except Exception:
            pass
        time.sleep(jps.TTL)


_ON_VERCEL = bool(
    os.environ.get("VERCEL")
    or os.environ.get("VERCEL_REGION")
    or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
)
if not _ON_VERCEL:
    threading.Thread(target=_jps_warm, daemon=True, name="jps-warmer").start()
