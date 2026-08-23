# DEMO.md — Banjir live demo

**Preview URL:** https://hackathon-claw-2026-pnb0g062j-kroevasuperadmins-projects.vercel.app

## Prereqs
- Python 3.11+
- `pip install -r requirements.txt`
- (Optional) Qwen key: copy `.env.example` to `.env` and fill `QWEN_API_KEY`

## Run local (any OS)
```bash
# Windows PowerShell
.\run_demo.ps1

# macOS / Linux
chmod +x run_demo.sh
./run_demo.sh
```

The script starts `uvicorn` on `http://127.0.0.1:8000` if it is not already listening, then calls `/api/status?place=Gombak`.

## What the judge should notice
1. **Live data:** response contains real JPS river levels for `Sg. Tua di Emp. Batu`, real MET warnings, and real MET forecast.
2. **Sources:** every card carries the publisher and a timestamp.
3. **Edge cases:**
   - Unknown place: `curl /api/status?place=Atlantis` returns `place_not_found: true` + suggestions.
   - Offline station: `curl /api/status?place=Kota%20Bharu` includes the Kedah/Kelantan stations marked `OFFLINE`.
   - JPS down: the API falls back to `BANJIR_JPS_CACHE`; the UI shows a `cached` badge.

## Web + pitch
1. Open `http://127.0.0.1:8000/` on a phone.
2. Type or tap the mic and say a place.
3. Tap **Let Banjir pitch** — the agent narrates a 30-second pitch using today's readings.

## Telegram (Hermes)
1. Copy `hermes/plugins/banjir/` to `%LOCALAPPDATA%\hermes\plugins\banjir` (Windows) or `~/.hermes/plugins/banjir` (macOS).
2. Set `BANJIR_API_BASE` to the Vercel URL.
3. `hermes plugins enable banjir && hermes gateway run`.
4. DM the bot: `Gombak banjir ke sekarang?`
