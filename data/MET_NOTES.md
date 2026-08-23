# MET Malaysia module — data/met.py

**Publisher:** MET Malaysia (Jabatan Meteorologi Malaysia), served by data.gov.my Realtime Weather API.
**Docs:** https://developer.data.gov.my/realtime-api/weather (the `/weather/warning` and `/weather/forecast` doc sub-pages 404 — everything is on the one page).

## Endpoints (trailing slash REQUIRED)
- `GET https://api.data.gov.my/weather/warning/` — live warnings (thunderstorm / strong wind & rough seas / "No Advisory" cyclone placeholder). Returned only current items (4 rows on 23 Aug 2026). Updated "when required".
- `GET https://api.data.gov.my/weather/forecast/` — 7-day forecast, 443 locations x 7 days = 3,101 rows. Updated daily.
- `GET https://api.data.gov.my/weather/warning/earthquake/` — not used.

## Query params (data.gov.my standard)
- `filter=<value>@<column>` exact (case-insensitive) · `contains=` / `icontains=` partial · `range=<col>[a:b]`
- `sort=col,-col2` · `limit=N` · `include=` / `exclude=` columns
- `date_start/date_end=YYYY-MM-DD@col` · `timestamp_start/timestamp_end=YYYY-MM-DD HH:MM:SS@col`
- Nested fields use `__`: `location__location_id`, `location__location_name`, `warning_issue__issued`, `warning_issue__title_en`
- Location ids: `St`=state (16), `Ds`=district (170), `Tn`=town (201), `Dv`=division (19), `Rc`=recreation centre (37). Example: `?contains=Ds058@location__location_id&sort=date` = Kuala Lumpur district.

## Rate limit (verified — hit it)
**4 requests/minute** per the docs; got HTTP 429 while testing. `met.py` disk-caches every response in `data/.met_cache.json` (warnings 5 min, forecast 60 min, location list 24 h) and serves the stale copy on 429/offline. Running `__main__` cold = exactly 4 calls.

## Field notes
- Forecast values are **Bahasa Melayu only** (`Tiada Hujan`, `Ribut petir di beberapa tempat`, ...). `met.py` maps them to EN from the docs table (`summary_en`, `summary_when_en`).
- Warning `valid_from/valid_to` are naive local (MYT) datetimes; `No Advisory` rows have `null` validity.
- **Affected areas are NOT a structured field.** `met.py` parses `text_en` ("...over the state of Sarawak: Sri Aman, Samarahan..." / "...over the waters of X until...") into `areas`. This is inferred, not official — say so in the UI.
- No flood warning endpoint here. MET = weather only; flood level = JPS (`data/jps.py`). `data.gov.my/flood-warning/` is a stale 2024 snapshot.

## Functions
- `warnings(include_expired=False)` -> list of dicts: `title_en/bm, heading_en, issued, valid_from, valid_to, text_en/bm, instruction_en/bm, areas (parsed), source`. Drops "No Advisory" and expired items.
- `forecast(location_name)` -> `{query, location_id, location_name, match_score, days:[{date, morning, afternoon, night, summary, summary_when, summary_en, summary_when_en, min_temp, max_temp}], source}` or `None`. Fuzzy match (difflib ≥0.6, substring ≥0.9, district beats town beats state on ties; aliases kl/pj/jb/kk/penang).
- `match_location(name)`, `locations()` helpers.

## Real output — `python data/met.py` (23 Aug 2026, 10:39 MYT)
```
# MET Malaysia — 2026-08-23 10:39 MYT — source: MET Malaysia via data.gov.my

## Active warnings: 3
- Strong Winds and Rough Seas Warning / Amaran Angin Kencang dan Laut Bergelora | issued 2026-08-23T09:00:00 | valid 2026-08-23T00:00:00 -> 2026-08-27T00:00:00
  areas (parsed): ['waters of Western Sarawak', 'waters of Phuket • Northern part of Reef North • Palawan • Layang-Layang • Northeastern Condore', 'waters of Reef South']
  text: SECTION A: FOR MALAYSIAN WATERS [WITHIN 24 NAUTICAL MILES] 1) THUNDERSTORMS WARNING Thunderstorms, heavy rain and strong winds are expected over the waters of Western Sarawak until 1:00 PM; Sunday, 23 August 2026. This condition may cause strong winds up to 50 kmph and rough seas with wave height up
- Strong Winds and Rough Seas Warning / Amaran Angin Kencang dan Laut Bergelora | issued 2026-08-23T09:00:00 | valid 2026-08-23T08:00:00 -> 2026-08-23T13:00:00
  areas (parsed): ['waters of Western Sarawak', 'waters of Phuket • Northern part of Reef North • Palawan • Layang-Layang • Northeastern Condore', 'waters of Reef South']
  text: SECTION A: FOR MALAYSIAN WATERS [WITHIN 24 NAUTICAL MILES] 1) THUNDERSTORMS WARNING Thunderstorms, heavy rain and strong winds are expected over the waters of Western Sarawak until 1:00 PM; Sunday, 23 August 2026. This condition may cause strong winds up to 50 kmph and rough seas with wave height up
- Thunderstorms Warning / Amaran Ribut Petir | issued 2026-08-23T09:00:00 | valid 2026-08-23T09:00:00 -> 2026-08-23T12:00:00
  areas (parsed): ['Sri Aman (Sarawak)', 'Samarahan (Sarawak)', 'Serian (Sarawak)', 'Betong (Sarawak)']
  text: Thunderstorms, heavy rain and strong winds are expected over the state of Sarawak: Sri Aman, Samarahan, Serian (Serian), Betong (Betong) until 12:00 PM; Sunday, 23 August 2026.

## Forecast: Kuala Lumpur -> Kuala Lumpur (Ds058, match 1.0)
- 2026-08-23: Tiada Hujan (No rain, Throughout the day) 25-34C
- 2026-08-24: Tiada Hujan (No rain, Throughout the day) 25-34C
- 2026-08-25: Ribut petir di beberapa tempat (Scattered thunderstorms, Morning) 25-34C
- 2026-08-26: Tiada Hujan (No rain, Throughout the day) 25-34C
- 2026-08-27: Tiada Hujan (No rain, Throughout the day) 25-34C
- 2026-08-28: Tiada Hujan (No rain, Throughout the day) 25-34C
- 2026-08-29: Tiada Hujan (No rain, Throughout the day) 25-34C

## Forecast: Gombak -> Gombak (Ds055, match 1.0)
- 2026-08-23: Tiada Hujan (No rain, Throughout the day) 24-34C
- 2026-08-24: Ribut petir di beberapa tempat (Scattered thunderstorms, Afternoon) 24-34C
- 2026-08-25: Ribut petir di beberapa tempat (Scattered thunderstorms, Morning and Afternoon) 24-34C
- 2026-08-26: Ribut petir di beberapa tempat (Scattered thunderstorms, Afternoon) 24-34C
- 2026-08-27: Tiada Hujan (No rain, Throughout the day) 24-34C
- 2026-08-28: Tiada Hujan (No rain, Throughout the day) 24-34C
- 2026-08-29: Tiada Hujan (No rain, Throughout the day) 24-34C
```
