#!/usr/bin/env python
"""
"Banjir, present yourself" — the agent-led pitch moment.
Run this ONE command on stage: it pulls today's real readings from the live
prod API and has the bot deliver its own presentation into Telegram, in the
chosen language. No manual typing, no waiting on Hermes tool-call latency —
guaranteed to land in <5s during the live demo.

Usage: python present_yourself.py [en|bm|zh] [chat_id]
"""
import json
import sys
import urllib.parse
import urllib.request

PROD = "https://banjirai.vercel.app"
BOT_TOKEN = "8786119365:AAFFuuArbsaza52vMq20MbU5wmAzBsCbMmw"
DEFAULT_CHAT = "5116627802"

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
CHAT = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CHAT

INTRO = {
    "en": "This is Banjir presenting itself to the judges.\n\n",
    "bm": "Ini Banjir memperkenalkan diri kepada juri.\n\n",
    "zh": "这是 Banjir 向评审自我介绍。\n\n",
}
OUTRO = {
    "en": "\n\nAsk me about any place in Malaysia, in English, Bahasa Malaysia or 中文.",
    "bm": "\n\nTanya saya tentang mana-mana kawasan di Malaysia, dalam English, Bahasa Malaysia atau 中文.",
    "zh": "\n\n用英语、马来语或中文问我马来西亚任何地方的情况。",
}


def fetch(url, timeout=25):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def pitch_for(place):
    url = f"{PROD}/api/pitch?place={urllib.parse.quote(place)}"
    return fetch(url)


def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    places = ["Gombak", "Shah Alam"]
    key = f"pitch_{LANG}"
    lines = []
    for p in places:
        d = pitch_for(p)
        line = d.get(key) or d.get("pitch_en") or ""
        lines.append(f"[{p}] {line}")

    message = INTRO.get(LANG, INTRO["en"]) + "\n\n".join(lines) + OUTRO.get(LANG, OUTRO["en"])
    print("--- MESSAGE ---")
    print(message)
    print("--- SENDING ---")
    result = send(CHAT, message)
    print("ok:", result.get("ok"))


if __name__ == "__main__":
    main()
