
# BANJIR — Hackathon Submission Pack

## PROBLEM STATEMENT

Flooding affects millions of Malaysians annually. According to verified data, the December 2024 east-coast floods displaced 150,832 people (44,336 families) nationwide (Malaymail). The economic impact is significant, with RM636.9m losses in 2025 alone (DOSM via NADMA). In urban areas, Kuala Lumpur alone has 14 identified flood hotspots (DBKL). Despite this, the government's flood data remains fragmented across multiple websites with no unified, user-friendly interface. The existing MyPublicInfoBanjir app has poor ratings (2.8/5) with users reporting offline water level data and limited functionality. The gap is clear: while authorities publish real-time flood data, Malaysians cannot easily ask "Is my area safe right now?" in plain Malay or English and receive a comprehensive answer.

## SOLUTION

Banjir is a web and Telegram-based flood awareness agent that provides real-time flood information in both Bahasa Malaysia and English. Users simply type their location to receive: (1) live water levels at nearby JPS river stations with Alert/Warning/Danger thresholds, (2) active MET Malaysia warnings for their area, (3) 24-hour weather forecasts, and (4) open JKM relief centres with evacuee counts. What sets Banjir apart is its integration of three official data sources (JPS, MET Malaysia, JKM) in one response, live per-station threshold monitoring, and honest reporting when data is unavailable. The solution is built using Devin as the AI coder, Hermes as the agent runtime, and Qwen to generate natural language explanations.

## 5-MINUTE PITCH

[0:00] Good morning, judges. I'm Faris Irfan, founder of Banjir. Let me start with a real scenario from this morning in Gombak. The Sg. Tua di Emp. Batu station was on ALERT at 103.21 meters, just 0.11 meters above the alert threshold of 103.10 meters. This is exactly the kind of information that can help residents take timely action before flooding worsens.

[1:00] [DEMO] Let me show you how Banjir works. I'll type "Gombak" into our web interface. Within seconds, you can see the nearest river stations with their current water levels and status. The system shows us that Sg. Tua di Emp. Batu is on ALERT, with the timestamp showing this data is live from JPS. We also see active MET Malaysia warnings for the area and a 24-hour forecast indicating heavy rain expected later today.

[2:00] [DEMO] Now let's check Shah Alam. You can see different river stations with their current levels compared to thresholds. Notice how each station's data clearly shows the publisher and timestamp - we never invent or estimate values. When a station is offline or has no threshold data, we honestly display "No reading" rather than showing potentially misleading information.

[3:00] [DEMO] Let's test an edge case by typing "Atlantis" - a location that doesn't exist in Malaysia. Instead of crashing or showing incorrect data, Banjir gracefully responds that it couldn't find the location and suggests nearby districts. This is crucial for user trust - we'd rather say "I don't know" than provide wrong information.

[4:00] The evidence shows why this solution is needed. Flooding affects 10.1% of Malaysia's land and approximately 5.67 million people. The economic impact is substantial, with RM636.9 million in losses in 2025 alone. Current solutions like the MyPublicInfoBanjir app have poor ratings and limited functionality. Our solution addresses these gaps by providing live, comprehensive flood information in an accessible format.

[5:00] What makes Banjir sustainable beyond today's hackathon? First, we use official data sources that are continuously maintained. Second, our architecture is lightweight and can be deployed anywhere. Third, we're exploring partnerships with schools and clinics through Helm AI to embed our service. Finally, our Telegram bot ensures we can reach users even without internet access.

[6:00] [DEMO] Let me show you our unique agent-led presentation feature. By clicking "Let Banjir pitch," the system will narrate a 30-second pitch using today's real flood readings. This demonstrates how AI can not only provide information but also communicate it effectively.

[7:00] In conclusion, Banjir addresses a real public problem by making critical flood information accessible to all Malaysians in their preferred language. We've built a working prototype that integrates multiple official data sources, handles edge cases gracefully, and provides value through both web and Telegram interfaces.

[8:00] I'd now like to address some likely questions:

Q: How fresh is your data?
A: Our JPS river level data updates every 5 minutes, MET warnings update when issued, and forecasts update daily. Each data point shows its exact timestamp and source.

Q: What happens if the JPS site goes down?
A: We cache the last good data and clearly show when it was last updated. We're transparent about data availability rather than showing outdated information as current.

Q: How is this different from the MyPublicInfoBanjir app?
A: Unlike the poorly rated official app, we provide live threshold comparisons, integrate multiple data sources, offer both BM and English, and work on both web and Telegram with a conversational interface.

## 1-MINUTE DEMO VIDEO SHOT LIST

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

6. [45-50s] Switching to Telegram interface
   Voiceover: "Access the same information through Telegram, even with limited internet."

7. [50-55s] Typing "Shah Alam" in Telegram and receiving response
   Voiceover: "The same comprehensive information is available through our Telegram bot."

8. [55-60s] Final screen showing "Let Banjir pitch" button being clicked
   Voiceover: "Banjir - keeping Malaysians informed and safe during flood events."

## README BLURB

Banjir is a Malaysian flood awareness agent that provides real-time flood information in both Bahasa Malaysia and English. By integrating data from JPS, MET Malaysia, and JKM, it delivers comprehensive flood status, warnings, forecasts, and relief centre information through web and Telegram interfaces. Built with Devin, Hermes, and Qwen, Banjir makes critical flood information accessible to all Malaysians.