# Banjir — a Malaysian flood-awareness agent

> Built at Devin × Claw Collective × Qwen AI Agents Hackathon 2026, Kuala Lumpur, 23 Aug 2026. Theme: AI for a Better Malaysia.

**Live demo:** `https://banjir.vercel.app` (replace with deployed URL) · **Run it:** see [DEMO.md](DEMO.md) · **Team:** Faris Irfan

## Verify it runs (10 seconds)

```bash
# 1. start (if not already running)
python -m uvicorn api.index:app --port 8000

# 2. smoke test — live JPS + MET data for Gombak
export BANJIR_API_BASE=http://127.0.0.1:8000   # Windows: $env:BANJIR_API_BASE="..."
curl -s "$BANJIR_API_BASE/api/status?place=Gombak" | python -m json.tool
```

Expected output (23 Aug 2026 ~11:10 MYT):

```
HTTP 200
place: Gombak
state: WP Kuala Lumpur
risk: ALERT
top station: Sg. Tua di Emp. Batu ALERT 103.21
forecast: Tiada Hujan / No rain
warnings: 3
relief available: True
```

Full JSON: top station `Sg. Tua di Emp. Batu` is at `ALERT` (level 103.21 m, alert=103.1, warning=104.1, danger=104.8), updated 10:50 MYT. MET active warnings and 24h forecast are returned with source and timestamp. No Qwen key is required — output falls back to deterministic BM/EN text.

## Problem Validity

Malaysians get flood warnings through disconnected official portals and one-way SMS. They cannot ask "is my area flooding?" in plain BM/English and get a live, sourced answer.

- **150,832 evacuees** (44,336 families) nationwide at the Dec 2024 east-coast peak — *Malay Mail, 1 Dec 2024* (EVIDENCE.md).
- **RM636.9 m flood losses in 2025** — *DOSM / NADMA, 16 Apr 2026* (EVIDENCE.md).
- **10.1% of Malaysian land is flood-prone; ~5.67 m people affected** — *JPS/DID baseline cited MDPI Water 2023* (EVIDENCE.md).
- **MyPublicInfoBanjir iOS app: 2.8/5** with reviews saying stations are "all offline" and the app cannot search a destination — *App Store, verified 23 Aug 2026* (EVIDENCE.md).

## Stack Integration

| Partner | Role | Where in repo | What happens at runtime |
|---|---|---|---|
| **Devin** (Cognition) | Built the repo and the API | `api/index.py`, `web/index.html`, `data/emergency.py` | Writes/updates the FastAPI app, the web page, and the emergency parser |
| **Hermes Agent** | Agent runtime | `hermes/plugins/banjir/`, `hermes/SOUL.md`, `hermes/SKILL.md` | Telegram bot calls `flood_status(place)` → `GET /api/status?place=`; web and Telegram share the same API |
| **Qwen 3.8** | LLM | `api/index.py` (`_qwen_call`) | Turns live readings into BM/EN explanation and narrated pitch; falls back to deterministic templates if the key is missing so the demo never dies |

Data sources at runtime: JPS Public InfoBanjir (`data/jps.py`), MET Malaysia via data.gov.my (`data/met.py`), JKM InfoBencana (`data/pps.py`), official hotlines + checklist (`data/EMERGENCY.md` → `data/emergency.py`).

## Functionality

- `GET /api/status?place=Gombak` — live JPS river stations with Alert/Warning/Danger thresholds, MET warnings, 24h forecast, relief centres, emergency checklist, hotlines.
- `GET /api/pitch?place=Gombak` — 30-second agent pitch in BM/EN using today's real readings.
- `GET /` — mobile-first web page: type or say a place, see cards, tap "Let Banjir pitch" for spoken narration.
- Three edge cases handled in the API and web:
  1. Unknown place → `place_not_found: true` + suggested nearby districts.
  2. Station offline / `-` values → JPS status = `OFFLINE`; UI shows "no reading".
  3. JPS site down → `api/index.py` falls back to last-good disk cache with a visible `cached` badge.

## Sustainability

- **Real problem, real data:** JPS, MET, JKM feeds are public and already maintained by Malaysian agencies.
- **No auth, low cost:** The app runs on free Vercel + public APIs. Qwen is optional.
- **Next steps (1 week):** (1) add geolocation via HTML5 + nearest station by district; (2) WhatsApp/Telegram broadcast for MET warning push; (3) partner with APM / district offices for the checklist.

## Assumptions & limits

- JPS has no public coordinates; "nearest" is by district/name match, not GPS.
- MET warnings do not have a structured "affected districts" field; filtering is by text match and may fall back to showing all active warnings.
- JKM PPS data lists open relief centres by state; per-centre timestamps are not exposed by the public endpoint.
- All river levels are from JPS gauges, not local street flooding.
- 10-second timeouts and 5-minute caches keep the demo responsive; first cold fetch can take ~12 seconds.
