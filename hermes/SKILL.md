# Banjir skill for Hermes

## Goal
Help Malaysians get live flood risk, official warnings, and what-to-do guidance for any place.

## When to use
- User asks about floods, banjir, river levels, rain, or evacuation.
- User asks for a demo / pitch.
- User says where they are.

## Tools
- `flood_status(place)` -> returns live JPS, MET, JKM, and hotline data.

## Output format
1. Reply in the language the user wrote in: Malay, English, or Chinese (Simplified, Malaysian-Chinese register).
2. State the risk level in the user's language.
3. Show the nearest station, its level vs threshold, and the last update time.
4. List any active MET warning for the state/area.
5. Give the 24h forecast.
6. Give the matching checklist and hotlines.
7. Cite the source every time. `flood_status` returns `en`, `bm`, and `zh` text; use the `zh` field when replying in Chinese.
