# JPS Public InfoBanjir — data notes

Publisher: Jabatan Pengairan dan Saliran (JPS) Malaysia, https://publicinfobanjir.water.gov.my. No JSON API exists; `data/jps.py` parses the same HTML tables the public page renders. Verified live 23 Aug 2026 ~10:30 MYT from the hackathon venue wifi.

## Endpoints (GET, no auth, 10s timeout)
- River levels (per state): `https://publicinfobanjir.water.gov.my/aras-air/data-paras-air/aras-air-data/?state={CODE}&district=ALL&station=ALL&lang=en`
  Columns: No, Station ID, Station Name, District, Main Basin, Sub River Basin, Last Updated (dd/mm/yyyy HH:MM), Water Level (m), Normal, Alert, Warning, Danger. Thresholds can be `-` (8 stations nationally).
- Rainfall (per state): `https://publicinfobanjir.water.gov.my/wp-content/themes/shapely/agency/searchresultrainfall.php?state={CODE}&district=ALL&station=ALL&loginStatus=0&language=1`
  This is the AJAX call the page `/hujan/data-hujan/?state={CODE}` makes (found in its `searchResult()` JS). `language=1` gives English headers; `language=en` returns blank headers. Columns: No, Station ID, Station, District, Last Updated (dd/mm/yyyy HH:MM:SS), 6 previous daily totals (mm), Rainfall from Midnight (today), Total 1 Hour (Now). `-9999.0` = no reading. JPS rain classes shown on the page: Light 1–10 mm, Moderate 11–30, Heavy 31–60, Very Heavy >60.
- `/hujan/data-hujan/data-hujan-data/` (guessed by analogy with aras-air-data) = 404. `/hujan/data-hujan/?state=X` alone = page shell with no data (loads via the AJAX URL above).
- The HTML is malformed (hundreds of stray `</tr>`, rainfall rows have no `<tr>`). Parser splits on the `<td data-th='No'>` cell; parsed row counts match raw marker counts for every state checked.

## State codes (from the `<select id="state">` on /aras-air/data-paras-air/)
| Code | State | WL stations | RF stations |
|---|---|---|---|
| PLS | Perlis | 8 | 21 |
| KDH | Kedah | 27 | 96 |
| PNG | Pulau Pinang | 19 | 47 |
| PRK | Perak | 28 | 49 |
| SEL | Selangor | 64 | 242 |
| WLH | WP Kuala Lumpur | 46 | 68 |
| PTJ | WP Putrajaya | 0 | 2 |
| NSN | Negeri Sembilan | 17 | 49 |
| MLK | Melaka | 23 | 40 |
| JHR | Johor | 74 | 150 |
| PHG | Pahang | 48 | 101 |
| TRG | Terengganu | 41 | 74 |
| KEL | Kelantan | 31 | 56 |
| SRK | Sarawak | 106 | 243 |
| SAB | Sabah | 4 | 21 |
| WLP | WP Labuan | 4 | 9 |
| MCK | Mockup/Pengujian (JPS test state — excluded) | – | – |

Total: 540 river-level stations, 1,268 rainfall stations.

## Status rules in `jps.py`
- `DANGER` / `WARNING` / `ALERT` = level >= that threshold (highest wins); `NORMAL` = below alert.
- `UNKNOWN` = level present but all thresholds `-` (JPS publishes no thresholds — we do not invent any).
- `OFFLINE` = no numeric level, or last update older than 24h (e.g. Sg. Sari, Kedah, last reading 20 Apr 2026 — shown on the site as a number, but it is not live).
- `fetch_all()` skips unreachable states and lists them in `jps.LAST_ERRORS` so the agent can disclose the gap.
- Cache: 5-minute in-memory per state; `fetch_all()` uses 8 threads (~4–9s cold, 0s warm).

## Gaps / honesty notes
- Putrajaya has 0 river-level stations on this page; Sabah only 4 (JPS publishes few there). Say so rather than "Putrajaya is safe".
- Station thresholds are JPS's, at the gauge. "Your area" is inferred by district/name fuzzy match (`nearest()`), not by geolocation — the page has no coordinates.
- Page rendering language and timestamp format may change; parser has no schema guarantee from JPS.

## Actual `python data/jps.py` output (23 Aug 2026)
```
JPS river levels, fetched 9.2s, 540 stations, 16 states
  PLS Perlis              8 stations  (0 offline/stale, 0 no thresholds)  
  KDH Kedah              27 stations  (1 offline/stale, 1 no thresholds)  
  PNG Pulau Pinang       19 stations  (0 offline/stale, 0 no thresholds)  
  PRK Perak              28 stations  (0 offline/stale, 0 no thresholds)  
  SEL Selangor           64 stations  (0 offline/stale, 0 no thresholds)  
  WLH WP Kuala Lumpur    46 stations  (0 offline/stale, 0 no thresholds)  
  PTJ WP Putrajaya        0 stations  (0 offline/stale, 0 no thresholds)  
  NSN Negeri Sembilan    17 stations  (0 offline/stale, 2 no thresholds)  
  MLK Melaka             23 stations  (0 offline/stale, 0 no thresholds)  
  JHR Johor              74 stations  (0 offline/stale, 4 no thresholds)  
  PHG Pahang             48 stations  (0 offline/stale, 1 no thresholds)  
  TRG Terengganu         41 stations  (0 offline/stale, 0 no thresholds)  
  KEL Kelantan           31 stations  (1 offline/stale, 0 no thresholds)  
  SRK Sarawak           106 stations  (0 offline/stale, 0 no thresholds)  
  SAB Sabah               4 stations  (0 offline/stale, 0 no thresholds)  
  WLP WP Labuan           4 stations  (0 offline/stale, 0 no thresholds)  

>= ALERT nationally: 3
  ALERT   KDH Sg. Kedah di Jambatan Lebuhraya [Kota Setar] 1.5 m (alert 1.5 / warn 1.8 / danger 2.1) @ 2026-08-23T10:00:00
  ALERT   WLH Sg. Tua di Emp. Batu [Gombak (WPKL)] 103.21 m (alert 103.1 / warn 104.1 / danger 104.8) @ 2026-08-23T09:25:00
  ALERT   PHG Sg. Luit di Kg. Subuh (F1) [Maran] 25.64 m (alert 25.5 / warn 26.0 / danger 27.5) @ 2026-08-23T10:30:00

nearest('Gombak'): [('Sg. Tua di Emp. Batu', 'ALERT'), ('Sg. Rawang di Taman Tun Teja', 'NORMAL'), ('Sg. Rawang di Rawang Tin', 'NORMAL'), ('Sg. Gong di Country Homes Rawang', 'NORMAL'), ('Sg. Kuang di Kg. Melayu Seri Kundang', 'NORMAL')]
nearest('KL'): [('Sg. Tua di Emp. Batu', 'ALERT'), ('Sg. Batu di Emp. Batu', 'NORMAL'), ('Sg. Bisul di Emp. Batu', 'NORMAL'), ('Empangan Klang Gates', 'NORMAL'), ('Sg. Batu di Saluran Keluar Empangan Batu (F2)', 'NORMAL')]

rainfall WLH: 68 stations, 0 with rain since midnight; sample: {'state': 'WLH', 'station_id': '0233061RF', 'name': 'Sg. Tua', 'district': 'Gombak (WPKL)', 'updated': '2026-08-23T09:25:00', 'daily_mm': {'17/08/2026': 0.5, '18/08/2026': 0.0, '19/08/2026': 0.0, '20/08/2026': 0.5, '21/08/2026': 0.0, '22/08/2026': 0.0}, 'today_mm': 0.0, 'last_hour_mm': 0.0}
```
