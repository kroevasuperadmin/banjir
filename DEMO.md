# DEMO.md — Banjir live demo

**Live URL:** https://banjirai.vercel.app

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
1. Open the live URL on a phone (or `http://127.0.0.1:8000/` locally).
2. Type or tap the mic and say a place. Switch the language pill to 中文.
3. Tap **Let Banjir pitch** — the agent narrates a 30-second pitch using today's readings.

## Telegram (Hermes)
1. Copy `hermes/plugins/banjir/` to `%LOCALAPPDATA%\hermes\plugins\banjir` (Windows) or `~/.hermes/plugins/banjir` (macOS).
2. Set `BANJIR_API_BASE` to the Vercel URL.
3. `hermes plugins enable banjir && hermes gateway run`.
4. DM the bot: `Gombak banjir ke sekarang?`

## THE WATCHER — live, unsolicited alert (the pitch's centrepiece)
"Banjir doesn't wait to be asked." One command pulls today's real JPS reading and pushes an alert into Telegram, exactly as a 24/7 background watcher would the moment a station crosses its threshold:
```bash
python scripts/force_alert.py Gombak en      # place, language (en|bm|zh)
```
Run it live on stage; the phone buzzes with the alert within seconds. Not staged data — Sg. Tua in Gombak really is on ALERT today.

## Agent-led presentation — "Banjir, present yourself"
The +2-point creativity moment: the agent introduces itself to the judges, in the chat, using this minute's numbers.
```bash
python scripts/present_yourself.py en        # language: en|bm|zh
```
Read the Telegram message straight off the phone. Full order and script: [PITCH.md](PITCH.md).
