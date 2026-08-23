# Implementation notes — Hermes and Devin Setup Workshop

- **What it is**
  - **Workshop:** Pre-hackathon setup walkthrough for Qwen, Hermes (presented as an OpenClaw-style persistent agent runtime), Telegram, and Devin.
  - **Core message:** Build with the agent beside you; use a persistent runtime with tools/memory, then use Devin to accelerate delivery.

- **Steal for today**
  - **What:** Put the one working agent in a real chat channel, not only a CLI. **Why:** Stronger **functionality** demo: a founder can send a real-world input and receive the output. **Where:** openclaw.json (Telegram channel setup) and DEMO.md (one send → one reply walkthrough).
  - **What:** Enable only the runtime capabilities the happy path uses: web/data lookup, browser/terminal, file operations, code execution, planning, memory, and job/task delegation. **Why:** Shows meaningful **stack integration** while keeping the demo reliable. **Where:** openclaw.json; explain each enabled tool in README.md’s Stack Integration table.
  - **What:** Add a small memory/skills layer: save repeated handling rules and the user’s business context. **Why:** Makes the agent more than a one-shot chatbot and supports **sustainability**. **Where:** skills/kira/SKILL.md and a minimal memory.md or project memory file documented in README.md.
  - **What:** Keep Devin Local pointed at this exact repo and use it to build/fix the bounded happy path. **Why:** Fast iteration improves **functionality**; the repo history proves the **Devin** part of the stack. **Where:** DEVIN_PROMPT.md, then commit the generated/fixed code in tools/ and link the Devin session in README.md.
  - **What:** Use the official Qwen endpoint/model ID as the runtime brain, and show one end-to-end Qwen-generated validation/explanation. **Why:** Direct, visible **stack integration** rather than a token configuration claim. **Where:** openclaw.json, skills/kira/SKILL.md, DEMO.md.
  - **What:** Capture the live flow as the pitch: input → agent → compliant JSON + BM/English missing-fields list. **Why:** The presenter explicitly says direct feature walkthroughs can outperform a rushed deck; this is the clearest **problem validity** and **functionality** proof. **Where:** DEMO.md, README.md, and demo recording/GIF.

- **Exact commands / configs / prompts shown**
  - **Command:** '/newbot' — typed in Telegram’s BotFather to create a Telegram bot.
  - **Config flow:** “Custom endpoint” → enter API base URL and API key → choose “OpenAI compatible server” → paste the full Qwen model ID → choose a display name.
  - **Config choices:** Presenter selected Telegram, then the BotFather option; selected the local/default runtime; and called out web search, browser automation, terminal, file operations, code execution, skills, task planning, memory, context engine, session search, task delegation, jobs, and computer use.
  - **Verbatim unavailable:** The installation line, base URL, model ID, and Hermes→Devin CLI prompt were screen-shared but are not legible/reliably transcribed in the available captions; none is reproduced here rather than guessed.

- **Contradicts the plan**
  - **Hermes vs OpenClaw:** The video recommends Hermes and calls it a better OpenClaw-style runtime; the scaffold requires OpenClaw. **Recommendation:** Do not switch today—keep OpenClaw so the judge sees the named required runtime, and borrow only the channel/memory/skills pattern.
  - **Devin usage:** The video’s main pattern is Devin as a coding assistant; the scaffold additionally requires runtime Devin API use. **Recommendation:** Keep tools/devin_builder.py; describe and demonstrate its fallback trigger so Devin is meaningful at runtime.
  - **Scope:** The video shows dashboards, Vercel/Supabase connections, parallel sessions, and 24/7 agent ideas. **Recommendation:** Do not add any of them unless the happy path already works; they violate the one-happy-path scope law.
  - **Channel risk:** The video suggests Telegram, while the plan allows terminal/Telegram/WhatsApp. **Recommendation:** Use Telegram only if setup succeeds quickly; otherwise ship the terminal demo.

- **Skip**
  - **Skip:** Hermes desktop UI, VPS/cloud hosting, iOS/Mac virtual-machine discussion, image generation, text-to-speech, and generic dashboard work.
  - **Skip:** Parallel Devin feature branches unless one person is actively reviewing merges; Faris is solo and has a short deadline.
  - **Skip:** Creating a pitch deck before the working demo, README evidence, and GIF exist.
