# Fix cycle 1 — verified against the running API at 11:33

Good: `/api/status?place=Gombak` and `?place=Shah Alam` return full live payloads; `/api/pitch` works with fallback; web page serves.

Fix these, in order, smallest diff each, run the check after each, commit after each with `devin:` prefix:

1. **`/api/status?place=Atlantis` returns HTTP 500.** Must return HTTP 200 JSON: `{"ok": false, "place_not_found": true, "place": "Atlantis", "suggestions": [...8 common districts...], "message_bm": "...", "message_en": "..."}`. Never 500 on user input. Check: `curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/api/status?place=Atlantis"` → 200.
2. **Cold request takes 21 s** (fetch_all over 16 states). Warm the JPS cache at startup (background thread on app start: `jps.fetch_all()`), and refresh it every 5 min in a background thread. Any request must answer in < 3 s once warm. Also: for a resolved place, only the matched state's stations are needed — use `jps.fetch_state(code)` (1 s) instead of `fetch_all()` when `places.resolve()` gives a state code. Check: time two consecutive `Gombak` requests; 2nd must be < 3 s.
3. **Unverified numbers in README.md and PITCH.md.** Remove "150,832 evacuees / 44,336 families" and "5.67 m people / 10.1% of land" (both UNVERIFIED in EVIDENCE.md). Replace with the VERIFIED set: RM933.4m flood losses in 2024 → RM636.9m in 2025 (DOSM via NADMA, 16 Apr 2026); Nov 2025 floods ~37,000 evacuees at peak across 7 states (JBA Risk); MyPublicInfoBanjir iOS app 2.8/5, last updated Nov 2022 (App Store). Keep publisher names. The rules say never present unverified data as fact.
4. **Vercel deployability.** Confirm `vercel.json` + `api/index.py` work as a Vercel Python serverless function (FastAPI via `@vercel/python`), with `web/index.html` served at `/`. Background threads don't persist on serverless: on Vercel, use per-request `fetch_state(code)` + the disk/in-memory cache, and keep `fetch_all()` only for unknown places. Make the data modules importable from `api/` on Vercel (sys.path / package layout). Do not deploy — just make `vercel build`-equivalent sanity pass locally if possible, and list any env vars needed.
5. **Stop the stray server** you left on port 8000 when done, and make `run_demo.ps1` / `run_demo.sh` kill-and-restart cleanly.
6. `git add -A && git commit` everything (including README/PITCH/DEMO and the new files) and `git push origin master`.

At the end print: the three curl checks with output, the commit hashes, and the env var list.
