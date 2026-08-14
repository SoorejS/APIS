# APIS Demo Script

**Target Duration:** 60-70 seconds
**Tone:** Confident, technical, authoritative (Datadog/Vercel style).
**Pacing:** Fast. No pauses. Read this with energy and a slight sense of urgency.

---

### [0:00 - 0:08] SCENE 1: THE PROBLEM
**Visual:** VS Code window with a static prompt string. The text `temperature=0` is visible. Hard cut to the APIS dark-mode Dashboard.
**Narration:**
"LLM systems silently degrade in production. A prompt that works today will inevitably suffer from 'model drift' tomorrow—hallucinating or ignoring constraints. Traditional infrastructure fails silently. APIS fixes this."

### [0:08 - 0:18] SCENE 2: LIVE DASHBOARD
**Visual:** Cursor panning smoothly across the `/runtime` metrics. Zooming slightly on the 'Average Latency' and 'Thumbs Down' graphs. 
**Narration:**
"APIS is an adaptive prompt infrastructure system. It continuously observes runtime behavior across multiple providers, tracking latency, token usage, and user feedback in real-time."

### [0:18 - 0:28] SCENE 3: FAILURE EVENT
**Visual:** Cut to `/drift`. The charts turn red. Cursor circles a massive spike in the 'Hallucination Rate' and 'Thumbs Down' graphs.
**Narration:**
"When an upstream model silently updates, your metrics tank. Here, a simulated drift event causes correctness to plummet and hallucinations to spike. Instead of waiting for users to complain, APIS detects the anomaly instantly."

### [0:28 - 0:45] SCENE 4: APIS RESPONSE (The 'Wow' Moment)
**Visual:** Fast transition to `/prompts`. Show a new 'Candidate' generated. Transition to `/canary`. Highlight the "10% Canary" traffic split, then show the rollback safety net UI.
**Narration:**
"This is where APIS takes over. It aggregates the failure logs and automatically generates a candidate prompt. It then safely routes 10% of production traffic to the canary. If latency spikes, APIS rolls it back automatically. If it succeeds, it heals the endpoint without human intervention."

### [0:45 - 0:55] SCENE 5: MATHEMATICAL VALIDATION
**Visual:** Cut to `/results`. Smooth scroll down the evaluation framework showing the Phase 7 benchmark deltas (MTTR reduced to 1.8h, Correctness +48%).
**Narration:**
"And we’ve mathematically validated this. Across a 14-day simulation with 12,000 interactions, the APIS adaptive feedback loop reduced hallucinations by 95% and recovered correctness in under two hours."

### [0:55 - 1:05] SCENE 6: ENDING HOOK
**Visual:** Quick cut to the GitHub README architecture diagram, zooming out to the repo header.
**Narration:**
"Prompt engineering is a manual band-aid. Prompt infrastructure is an autonomous immune system. APIS is fully open-source. Check out the GitHub repo to deploy it today."
