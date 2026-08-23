"""Banjir plugin — one tool, flood_status(place), backed by our own HTTP API."""
import json
import os
import urllib.parse
import urllib.request

API_BASE = os.environ.get("BANJIR_API_BASE", "http://localhost:8000")

FLOOD_STATUS = {
    "name": "flood_status",
    "description": (
        "Live Malaysian flood status for a place (district/town/kampung). "
        "Returns nearest JPS river stations with current level vs Alert/Warning/Danger "
        "thresholds, active MET Malaysia warnings, 24h forecast, what-to-do checklist, "
        "hotlines, and the source + timestamp for every number. Call this for ANY "
        "'is my area flooding / banjir' question. Never guess flood data yourself."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "place": {
                "type": "string",
                "description": "Place name as the user said it, e.g. 'Gombak', 'Kg Baru KL', 'Kota Bharu'",
            },
        },
        "required": ["place"],
    },
}


def flood_status(args: dict, **kwargs) -> str:
    place = (args.get("place") or "").strip()
    if not place:
        return json.dumps({"error": "place is required"})
    url = f"{API_BASE}/api/status?place={urllib.parse.quote(place)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:  # ponytail: no retry; API caches 5 min itself
            return r.read().decode("utf-8")
    except Exception as e:
        return json.dumps({"error": f"Banjir API unreachable: {e}", "url": url,
                           "hint": "Say the live feed is down; give hotlines from EMERGENCY.md."})


def register(ctx):
    ctx.register_tool(
        name="flood_status",
        toolset="banjir",
        schema=FLOOD_STATUS,
        handler=flood_status,
        emoji="🌊",
    )


if __name__ == "__main__":  # python hermes/plugins/banjir/__init__.py  (needs API running)
    assert json.loads(flood_status({"place": ""}))["error"]
    print(flood_status({"place": "Gombak"})[:300])
