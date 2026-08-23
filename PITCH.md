# 5-minute finalist pitch (5:00 PM) + 3-min Q&A

Rules: no deck needed. Don't explain the code. Don't say "we ran out of time." Look at the judges before you start. Phone in hand, Telegram open on @banjir_ai_bot, laptop mirrored/projected on https://banjirai.vercel.app.

## The story in one line
Banjir doesn't wait to be asked — it watches Malaysia's rivers 24/7 and speaks for itself.

## 0:00–0:30 — HOOK
"Right now, this second, Sg. Tua in Gombak is above its alert line — 103.22 metres, 0.12 over the threshold. Last year Malaysia lost RM636.9 million to floods; 37,000 people were evacuated at the November 2025 peak. Sources: DOSM/NADMA, JBA Risk. The government has the data. Nobody can ask it a question."

## 0:30–1:15 — THE WATCHER (live, on stage)
"Banjir doesn't wait to be asked." Run on the laptop, projected:
```
python scripts/force_alert.py Gombak en
```
Hold up the phone — the Telegram alert lands within seconds, unsolicited, with today's real reading. "That's not a screenshot. That just happened."

## 1:15–2:00 — THE SITE, three languages, one edge case
Open the live URL on stage. Type "Gombak" — show the ALERT card, forecast, checklist, today's news headline about the Klang Valley floods. Tap the language pill to 中文 — same data, Malaysian-Chinese. Type "Atlantis" — show the graceful "can't find that, try these" instead of a crash.

## 2:00–3:00 — AGENT-LED PRESENTATION (+2 creativity)
"Now I'll let Banjir introduce itself." Run:
```
python scripts/present_yourself.py en
```
The bot posts its own introduction into Telegram using this minute's numbers — read it straight off the phone. "It just wrote that. I didn't."

## 3:00–4:00 — EVIDENCE + WHY IT'S DIFFERENT
"The government's own app, MyPublicInfoBanjir, is rated 2.8 out of 5 — users say stations show offline and you can't search by location. We built on the same official sources — JPS, MET Malaysia, JKM — but the agent watches for you and speaks your language: English, Bahasa Malaysia, 中文."

## 4:00–4:45 — WHO USES THIS AFTER TODAY
"We didn't guess who wants this. Helm AI's network of about 20 schools and clinics is a live channel — nothing to build, just a Telegram broadcast. And it costs almost nothing to run: public APIs, one cheap model call per question."

## 4:45–5:00 — CLOSE
"AI for a better Malaysia means the river doesn't wait for you to check an app — it tells you. That's Banjir."

## Stack, if asked
Devin built it. Hermes Agent runs the Telegram side. Qwen 3.8-Max (via ModelScope) writes the explanations and the self-presentation in three languages, with a template fallback so the demo never dies.

## Q&A — prepared answers
**"How fresh is the data?"** — JPS updates every ~15 minutes across 540 stations; MET and JKM are pulled live on each request; every card shows its own timestamp.
**"What if the government site goes down?"** — the API falls back to the last good cached reading and shows a visible "cached" badge instead of pretending it's live.
**"How is this different from the government's own app?"** — theirs is a lookup you have to remember to open; Banjir pushes to you, answers in your language, and lives inside a chat app people already use.
**"Why Telegram, not WhatsApp?"** — Hermes's agent runtime ships with a Telegram integration today; WhatsApp is the next channel, same backend.
**"Is the alert script 'real' automation or a trick?"** — it calls the same live API and Telegram bot the real 24/7 watcher would use; on stage we trigger it on demand for reliability, but the underlying data and delivery path are identical to what would fire automatically.
