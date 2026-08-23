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
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

load_dotenv()

# Make repo root importable from this package both locally and on Vercel
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data import emergency, jps, met, news, places, pps

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
# Keywords a MET warning must mention to be shown for a state
STATE_KEYWORDS = {
    "perlis": ["perlis", "kedah & perlis", "semenanjung", "peninsular", "peninsula"],
    "kedah": ["kedah", "perlis & kedah", "penang & kedah", "semenanjung", "peninsular", "peninsula"],
    "pulau pinang": ["pulau pinang", "penang", "perlis & kedah", "semenanjung", "peninsular", "peninsula"],
    "perak": ["perak", "penang & perak", "semenanjung", "peninsular", "peninsula"],
    "selangor": ["selangor", "kuala lumpur", "wp kuala lumpur", "negeri sembilan", "semenanjung", "peninsular", "peninsula"],
    "wp kuala lumpur": ["kuala lumpur", "wp kuala lumpur", "wilayah persekutuan", "selangor", "semenanjung", "peninsular", "peninsula"],
    "wp putrajaya": ["putrajaya", "wilayah persekutuan", "selangor", "semenanjung", "peninsular", "peninsula"],
    "negeri sembilan": ["negeri sembilan", "selangor", "melaka", "semenanjung", "peninsular", "peninsula"],
    "melaka": ["melaka", "malacca", "negeri sembilan", "johor", "semenanjung", "peninsular", "peninsula"],
    "johor": ["johor", "pahang", "semenanjung", "peninsular", "peninsula"],
    "pahang": ["pahang", "perak", "selangor", "johor", "terengganu", "semenanjung", "peninsular", "peninsula"],
    "terengganu": ["terengganu", "kelantan", "pahang", "semenanjung", "peninsular", "peninsula"],
    "kelantan": ["kelantan", "terengganu", "semenanjung", "peninsular", "peninsula"],
    "sarawak": ["sarawak", "borneo", "east malaysia"],
    "sabah": ["sabah", "borneo", "east malaysia"],
    "wp labuan": ["labuan", "sabah", "borneo", "east malaysia"],
}


def _warning_matches_state(w, state_name, place):
    """True if the warning's text/areas mention this state, its neighbours, or Peninsular Malaysia."""
    if not state_name:
        return True
    state_clean = state_name.lower().replace("wp ", "")
    keywords = STATE_KEYWORDS.get(state_clean, [state_clean])
    text = " ".join([w.get("title_en") or "", w.get("title_bm") or "",
                     w.get("text_en") or "", w.get("text_bm") or ""]).lower()
    all_text = text + " " + " ".join(a.lower() for a in w.get("areas", []))
    return any(k in all_text for k in keywords)


def _filter_warnings(warnings, state_name, place):
    """Return only MET warnings that mention the resolved state/area."""
    if not state_name:
        return warnings[:5]
    return [w for w in warnings if _warning_matches_state(w, state_name, place)][:5]


_PERIOD_BM = {"morning": "Pagi", "afternoon": "Petang", "night": "Malam"}


def _next_24h(forecast):
    if not forecast or not forecast.get("days"):
        return None
    today = forecast["days"][0]
    tomorrow = forecast["days"][1] if len(forecast["days"]) > 1 else None
    periods = []
    for label in ("morning", "afternoon", "night"):
        periods.append({
            "when_en": label.capitalize(),
            "when_bm": _PERIOD_BM[label],
            "summary_bm": today.get(label, ""),
            "summary_en": met.FORECAST_EN.get((today.get(label) or "").lower(), today.get(label, "")),
        })
    if tomorrow:
        for label in ("morning", "afternoon", "night"):
            periods.append({
                "when_en": f"Tomorrow {label.capitalize()}",
                "when_bm": f"{_PERIOD_BM[label]} esok",
                "summary_bm": tomorrow.get(label, ""),
                "summary_en": met.FORECAST_EN.get((tomorrow.get(label) or "").lower(), tomorrow.get(label, "")),
            })
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
        "periods": periods,
        "source": "MET Malaysia via data.gov.my",
    }


def _relief(state_name, place):
    """Return relief centres for the state, plus a national summary when the state has none open."""
    d = pps.open_pps(state_name.lower() if state_name else None)
    if not d.get("available"):
        return {
            "available": False,
            "reason": d.get("reason", "JKM InfoBencana unavailable"),
            "dashboard_url": d.get("dashboard_url", "https://infobencanajkmv2.jkm.gov.my/landing/"),
            "source": "JKM InfoBencana",
        }
    centres = d.get("centres", [])
    flood = [c for c in centres if "banjir" in (c.get("disaster") or "").lower()]
    top = (flood or centres)[:3]
    national = None
    if not top:
        nd = pps.open_pps()
        if nd.get("available"):
            national = {
                "count": nd.get("count", 0),
                "states": sorted({c["state"] for c in nd["centres"] if c.get("state")})[:5],
                "disaster_types": sorted({c["disaster"] for c in nd["centres"] if c.get("disaster")})[:3],
            }
    return {
        "available": True,
        "count": d.get("count"),
        "flood_count": d.get("flood_count"),
        "evacuees": d.get("evacuees"),
        "fetched_at": d.get("fetched_at"),
        "source": d.get("source"),
        "dashboard_url": d.get("dashboard_url"),
        "centres": top,
        "national": national,
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

    return {"en": en, "bm": bm, "risk_level": status, "risk_color": RISK_COLOR.get(status, "gray")}


def _extract_json(text):
    """Qwen sometimes wraps JSON in markdown fences; extract the inner JSON."""
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    if m:
        text = m.group(1)
    text = text.strip()
    try:
        data = json.loads(text)
        if "en" in data and "bm" in data:
            return {"en": data.get("en"), "bm": data.get("bm")}
    except Exception:
        pass
    return None


def _qwen_call(prompt, fallback_dict, max_tokens=200):
    """Call Qwen/ModelScope if configured; otherwise return the deterministic fallback."""
    key = os.environ.get("QWEN_API_KEY")
    base = os.environ.get("QWEN_BASE_URL", "https://api-inference.modelscope.ai/v1")
    model = os.environ.get("QWEN_MODEL", "Qwen-Ambassador/Qwen3.8-Max")
    if not key:
        return dict(fallback_dict, fallback=True, model=None, llm_error="QWEN_API_KEY not set")

    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": max_tokens,
                "enable_thinking": False,
            },
            timeout=20,
        )
        r.raise_for_status()
        payload = r.json()
        text = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if not text:
            return dict(fallback_dict, fallback=True, model=model, llm_error="empty content from Qwen")

        parsed = _extract_json(text)
        if parsed:
            return {"en": parsed["en"], "bm": parsed["bm"], "fallback": False, "model": model}

        # Non-JSON but valid text: use the whole text for both languages as a last resort
        return {"en": text, "bm": text, "fallback": False, "model": model}
    except Exception as e:
        return dict(fallback_dict, fallback=True, model=model, llm_error=str(e))


def _compact(data):
    """Strip the Qwen prompt down to the numbers it actually needs."""
    top = data.get("top_station") or {}
    return {
        "place": data.get("place"),
        "state": data.get("state"),
        "risk": data.get("risk"),
        "station_name": top.get("name"),
        "station_district": top.get("district"),
        "station_level": top.get("level"),
        "station_status": top.get("status"),
        "thresholds": {
            "normal": top.get("normal"),
            "alert": top.get("alert"),
            "warning": top.get("warning"),
            "danger": top.get("danger"),
        },
        "trend": top.get("trend"),
        "warnings_count": data.get("warnings_count"),
        "forecast_en": data.get("forecast_en"),
        "forecast_bm": data.get("forecast_bm"),
        "relief_count": data.get("relief_count"),
    }


def _status_summary(data):
    """Turn a full /api/status response into a small Qwen prompt."""
    top = (data.get("jps") or {}).get("stations", [None])[0]
    forecast = data.get("met_forecast") or {}
    return {
        "place": data.get("place"),
        "state": data.get("resolved_state"),
        "top_station": top,
        "risk": data.get("emergency", {}).get("risk_level"),
        "warnings_count": len(data.get("met_warnings", [])),
        "forecast_en": forecast.get("summary_en"),
        "forecast_bm": forecast.get("summary_bm"),
        "relief_count": (data.get("relief_centres") or {}).get("count"),
    }


def _qwen_explanation(place, data, fallback):
    compact = _compact(data)
    prompt = (
        "Return JSON {en, bm}. ~25 words each. "
        f"Place: {place}. State: {compact.get('state')}. "
        f"Station: {compact.get('station_name')} ({compact.get('station_district')}). "
        f"Level: {compact.get('station_level')} m. Status: {compact.get('station_status')}. "
        f"Thresholds: N={compact.get('thresholds', {}).get('normal')} A={compact.get('thresholds', {}).get('alert')} "
        f"W={compact.get('thresholds', {}).get('warning')} D={compact.get('thresholds', {}).get('danger')}. "
        f"Trend: {compact.get('trend')}. Warnings: {compact.get('warnings_count')}. "
        f"Forecast: {compact.get('forecast_en')} / {compact.get('forecast_bm')}."
    )
    return _qwen_call(prompt, fallback, max_tokens=120)


def _qwen_pitch(place, data, fallback):
    compact = _compact(data)
    prompt = (
        "Return JSON {en, bm}. ~60 words each. Sell Banjir as a live flood agent. "
        f"Place: {place}. State: {compact.get('state')}. "
        f"Station: {compact.get('station_name')}. Level: {compact.get('station_level')} m. "
        f"Status: {compact.get('station_status')}. Alert: {compact.get('thresholds', {}).get('alert')}. "
        f"Trend: {compact.get('trend')}. Forecast: {compact.get('forecast_en')} / {compact.get('forecast_bm')}."
    )
    return _qwen_call(prompt, fallback, max_tokens=220)


# ---------------------------------------------------------------------------
# Status data (used by both /api/status and /api/pitch)
# ---------------------------------------------------------------------------
def _status_core(place: str, include_news: bool = True):
    t0 = time.time()
    place = place.strip()

    # 1. resolve place: if the gazetteer gives a state, fetch only that state
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
            "message_en": f"We couldn't find '{place}'. Try one of these nearby areas:",
            "message_bm": f"Kami tidak jumpa '{place}'. Cuba kawasan berikut:",
            "generated_at": _now().isoformat(),
            "sources": [{
                "name": "JPS Malaysia",
                "url": "https://publicinfobanjir.water.gov.my",
                "status": "no station match",
            }],
        }

    # 4. attach trend using state rainfall
    _attach_trend(nearest, state_code)

    # 5. resolve a better forecast if place didn't match
    if not forecast:
        for candidate in [nearest[0].get("district"), state_name]:
            if candidate:
                forecast = met.forecast(candidate)
                if forecast:
                    break

    # 6. filter warnings + relief by resolved state; keep national warnings for the UI
    all_warnings = warnings
    warnings = _filter_warnings(warnings, state_name, place)
    relief = _relief(state_name, place)

    # 7. news (fetched by /api/status in parallel with Qwen)
    news_items = []

    # 8. risk + emergency
    risk = _top_risk(nearest)
    hotlines = emergency.hotlines_for(state_name or "")
    checklist = emergency.checklist_for(risk)

    # 9. source / freshness notes
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
        "met_warnings_all_count": len(all_warnings),
        "met_warnings_all_summary": [{"title_en": w.get("title_en"), "title_bm": w.get("title_bm"), "areas": w.get("areas")} for w in all_warnings],
        "met_forecast": _next_24h(forecast),
        "relief_centres": relief,
        "news": news_items,
        "emergency": {
            "risk_level": risk,
            "risk_color": RISK_COLOR.get(risk, "gray"),
            "hotlines": hotlines,
            "checklist": checklist,
        },
        "sources": [
            {"name": "JPS Malaysia", "url": "https://publicinfobanjir.water.gov.my", "fetched_at": jps_fresh},
            {"name": "MET Malaysia", "url": "https://api.data.gov.my/weather", "fetched_at": _now().isoformat()},
            {"name": "JKM InfoBencana", "url": "https://infobencanajkmv2.jkm.gov.my/landing/", "fetched_at": relief.get("fetched_at")},
            {"name": "NADMA / APM hotlines", "url": "https://www.civildefence.gov.my/hotline-apm/", "fetched_at": _now().isoformat()},
        ],
    }
    return response


def _explain_data(data):
    forecast = data.get("met_forecast") or {}
    top = (data.get("jps") or {}).get("stations", [None])[0]
    return {
        "place": data.get("place"),
        "state": data.get("resolved_state"),
        "top_station": top,
        "risk": data.get("emergency", {}).get("risk_level"),
        "warnings_count": len(data.get("met_warnings", [])),
        "forecast_en": forecast.get("summary_en"),
        "forecast_bm": forecast.get("summary_bm"),
        "relief_count": (data.get("relief_centres") or {}).get("count"),
    }


# ---------------------------------------------------------------------------
# /api/status
# ---------------------------------------------------------------------------
@app.get("/api/status")
def status(place: str = Query(..., min_length=1, description="Place name in Malaysia")):
    t0 = time.time()
    data = _status_core(place, include_news=False)
    if not data.get("ok"):
        return JSONResponse(data)

    # Fetch news and Qwen explanation in parallel to keep the function under 60s
    fallback_explain = _build_explanation(
        data["place"], data["jps"]["stations"], data["emergency"]["risk_level"],
        data["met_forecast"], data["met_warnings"], data["relief_centres"]
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        news_future = ex.submit(news.news, data.get("resolved_state") or data.get("place") or place, "banjir")
        explain_future = ex.submit(_qwen_explanation, data["place"], _explain_data(data), fallback_explain)

    data["news"] = news_future.result()
    explain = explain_future.result()
    explain.setdefault("risk_level", data["emergency"]["risk_level"])
    explain.setdefault("risk_color", data["emergency"]["risk_color"])
    data["explanation"] = explain
    data["request_seconds"] = round(time.time() - t0, 2)
    return JSONResponse(data)


# ---------------------------------------------------------------------------
# /api/pitch
# ---------------------------------------------------------------------------
@app.get("/api/pitch")
def pitch(place: str = Query(..., min_length=1, description="Place name in Malaysia")):
    try:
        data = _status_core(place, include_news=False)
    except Exception as e:
        data = {"ok": False, "error": str(e)}

    fallback = {
        "en": (f"This is Banjir. I just checked river levels, MET warnings, the forecast, and relief centres for {place}. "
               "Get live flood status in Bahasa Malaysia and English, anytime."),
        "bm": (f"Ini Banjir. Baru sahaja saya semak data sungai, amaran MET, ramalan, dan pusat pemindahan untuk {place}. "
               "Dapatkan status banjir terkini dalam Bahasa Malaysia dan English pada bila-bila masa."),
    }

    pitch = _qwen_pitch(place, _status_summary(data), fallback)
    return JSONResponse({
        "ok": data.get("ok", False),
        "place": place,
        "pitch_en": pitch.get("en"),
        "pitch_bm": pitch.get("bm"),
        "fallback": pitch.get("fallback", True),
        "model": pitch.get("model"),
        "llm_error": pitch.get("llm_error"),
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
