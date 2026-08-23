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
1. State the risk level in BM + EN.
2. Show the nearest station, its level vs threshold, and the last update time.
3. List any active MET warning for the state/area.
4. Give the 24h forecast.
5. Give the matching checklist and hotlines.
6. Cite the source every time.
