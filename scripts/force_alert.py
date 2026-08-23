#!/usr/bin/env python
"""
THE WATCHER — proactive alert demo.
"Banjir doesn't wait to be asked." Run this ONE command on stage: it pulls
the real live JPS reading for a place and has the bot push an unsolicited
alert into Telegram — the exact message a background watcher would send the
moment a station crosses its threshold. Today Sg. Tua in Gombak really is on
ALERT, so this is not staged data, only a staged trigger.

Usage: python force_alert.py [place] [en|bm|zh] [chat_id]
"""
import json
import sys
import urllib.parse
import urllib.request

PROD = "https://hackathon-claw-2026.vercel.app"
BOT_TOKEN = "8786119365:AAFFuuArbsaza52vMq20MbU5wmAzBsCbMmw"
DEFAULT_CHAT = "5116627802"

PLACE = sys.argv[1] if len(sys.argv) > 1 else "Gombak"
LANG = sys.argv[2] if len(sys.argv) > 2 else "en"
CHAT = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_CHAT

HEADER = {"en": "⚠️ BANJIR WATCHER ALERT", "bm": "⚠️ AMARAN PEMANTAU BANJIR", "zh": "⚠️ BANJIR 监测警报"}
DO_NOW = {
    "en": "Do now: stay alert, prepare an emergency bag, watch for updates.",
    "bm": "Buat sekarang: berjaga-jaga, sediakan beg kecemasan, pantau perkembangan.",
    "zh": "现在就做：保持警惕，准备应急包，留意最新消息。",
}


def fetch(url, timeout=25):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    d = fetch(f"{PROD}/api/status?place={urllib.parse.quote(PLACE)}")
    jps = d.get("jps", {})
    stations = jps.get("nearest") or jps.get("stations") or []
    top = stations[0] if stations else {}

    header = HEADER.get(LANG, HEADER["en"])
    name = top.get("name", "?")
    district = top.get("district", d.get("resolved_state", PLACE))
    level = top.get("level")
    status = top.get("status", "?")
    alert = top.get("alert")
    updated = top.get("updated") or jps.get("fetched_at", "")
    do_now = DO_NOW.get(LANG, DO_NOW["en"])

    message = (
        f"{header}\n\n"
        f"{name} ({district})\n"
        f"Level: {level} m — status: {status} (alert line: {alert} m)\n"
        f"Updated: {updated}\n\n"
        f"{do_now}\n\n"
        f"Source: JPS Malaysia (publicinfobanjir.water.gov.my)"
    )
    print("--- MESSAGE ---")
    print(message)
    print("--- SENDING ---")
    result = send(CHAT, message)
    print("ok:", result.get("ok"))


if __name__ == "__main__":
    main()
