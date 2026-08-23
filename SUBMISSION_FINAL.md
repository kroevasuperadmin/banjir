
### GROUP NAME
Banjir

### PROBLEM STATEMENT (≤150 words) [148 words]
Today at 11:55, Sg. Tua di Emp. Batu in Gombak reads 103.21 m, above its 103.10 m ALERT line (JPS). Today's headline: "Lima tindakan segera tangani banjir di Lembah Klang" (Berita Harian/Astro Awani/Kosmo, 23 Aug 2026). Floods are a now problem, not a monsoon-season problem. The public (residents, parents, small traders) in flood-prone districts need immediate answers. Currently, they must check multiple government portals and use the MyPublicInfoBanjir iOS app (2.8/5 rating, last updated Nov 2022), which users complain shows stations as "offline" and lacks location search. The gap: nobody can ask "is my area OK right now?" in their own language and get a sourced answer. With RM933.4 million in flood losses in Malaysia in 2024 (DOSM via NADMA), and about 37,000 evacuees at peak during Nov 2025 floods (JBA Risk), this information gap poses real risks.

### SOLUTION (≤150 words) [149 words]
Banjir is a live agent (web + Telegram) that answers "Is my area safe now?" in English, Bahasa Malaysia, or 中文. When users enter a location, it returns: (1) live JPS river stations with official Alert/Warning/Danger thresholds, (2) MET Malaysia warnings for their state, (3) 24-hour forecast, (4) open JKM relief centres with evacuee counts, (5) what-to-do checklist + official hotlines, and (6) latest news for their state. What sets it apart: live per-station thresholds from 540 JPS stations; three official publishers + news in one answer; trilingual support; web + Telegram access; honest "no data" display; and an AI agent that narrates a 30-second pitch using today's real numbers. Stack: Devin built it, Hermes Agent runs the Telegram agent with a custom flood_status tool, Qwen 3.8-Max (via ModelScope) writes explanations in 3 languages.

### 5-MINUTE PITCH (spoken, ~650 words, [DEMO] cues, timestamps each ~60 s)
See [PITCH.md](PITCH.md) for the current, rehearsed script — updated to lead with THE WATCHER (a live, on-stage unsolicited flood alert triggered by `scripts/force_alert.py`) and the agent-led presentation moment (`scripts/present_yourself.py`, +2 creativity points), plus prepared Q&A answers.


### 1-MINUTE DEMO VIDEO SHOT LIST
1. [0-5s] Close-up of phone screen showing Banjir web interface with location input field
   Voiceover: "Banjir helps Malaysians get real-time flood information in their preferred language."

2. [5-15s] Typing "Gombak" into the search field
   Voiceover: "Simply type where you are to get instant flood information."

3. [15-25s] Results page showing river stations with water levels and thresholds
   Voiceover: "See live water levels at nearby JPS stations compared to Alert, Warning, and Danger thresholds."

4. [25-35s] Scrolling to show MET Malaysia warnings and 24-hour forecast
   Voiceover: "Get official weather warnings and forecasts for your area."

5. [35-45s] Showing relief centres and emergency contacts
   Voiceover: "Find open relief centres and emergency hotlines when needed."

6. [45-50s] Tapping language button to switch to 中文
   Voiceover: "Access information in English, Bahasa Malaysia, or 中文."

7. [50-55s] Typing "Atlantis" and receiving suggestion response
   Voiceover: "Banjir handles unknown locations gracefully with suggestions."

8. [55-60s] Final screen showing Telegram bot answering a query
   Voiceover: "The same comprehensive information is available through our Telegram bot."

### README BLURB
Banjir is a Malaysian flood awareness agent that provides real-time flood information in English, Bahasa Malaysia, and 中文. By integrating data from JPS, MET Malaysia, and JKM, it delivers integrated flood status, warnings, forecasts, and relief centre information through web and Telegram interfaces. Built with Devin (AI coder), runs on Hermes (agent runtime), Qwen generates natural language explanations.