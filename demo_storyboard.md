# APIS Demo: Shot-by-Shot Storyboard

To achieve Vercel/Datadog-level quality, your screen recording must be perfectly choreographed. No erratic mouse movements. No fumbling. 

---

### Shot 1: The Status Quo (0:00 - 0:08)
- **Screen:** VS Code open to `backend/api/v1/dashboard.py` or a dummy prompt file.
- **Action:** Mouse is still. Code is highlighted.
- **Transition (0:05):** Hard, instant cut to the APIS Dashboard (`/`). No fade. Hard cuts feel technical and fast.

### Shot 2: Observability Panning (0:08 - 0:18)
- **Screen:** APIS Dashboard (`/runtime`).
- **Action:** 
  1. Mouse starts off-screen.
  2. Smoothly glide the mouse down the left sidebar to click "Runtime".
  3. Once the charts load, trace the mouse over the "Average Latency" trendline so the Recharts tooltip appears. 
  4. Move smoothly to hover over the "Thumbs Down" bar chart.

### Shot 3: The Drift Injection (0:18 - 0:28)
- **Screen:** APIS Dashboard (`/drift`).
- **Action:**
  1. Click "Drift" in the sidebar.
  2. The screen shows the red "Threshold Breach" alerts.
  3. Mouse moves slowly to highlight the "Hallucination Rate Spike" card. 
  4. Do a slow, 10% digital zoom-in (using OBS or post-production software) on the red warning badge.

### Shot 4: The Adaptive Engine (0:28 - 0:45)
- **Screen:** Rapid succession across `/prompts` and `/canary`.
- **Action:**
  1. Click "Prompts" in the sidebar.
  2. Expand a timeline card to show the "Diff" between v1.0 and Candidate v1.1. Move mouse to highlight the green added lines.
  3. Click "Canary" in the sidebar.
  4. Hover over the "10% Canary Active" badge.
  5. Hover over the "Rollback" and "Promote" buttons to show they are interactable.

### Shot 5: The Proof (0:45 - 0:55)
- **Screen:** APIS Dashboard (`/results`).
- **Action:**
  1. Click "Eval Proof" in the sidebar.
  2. Scroll down *smoothly* (use arrow keys or a smooth-scroll mouse wheel) to reveal the "Correctness Degradation & Auto-Healing" Area chart.
  3. Hover the mouse directly over the dashed "Drift Injected" vertical line, showing the baseline tanking while the adaptive line recovers.

### Shot 6: The Call to Action (0:55 - 1:05)
- **Screen:** APIS GitHub Repository (`README.md`).
- **Action:**
  1. Cut to the browser showing the top of the GitHub repo.
  2. Smoothly scroll down to the "High-Level System Architecture" Mermaid diagram.
  3. Hold for 3 seconds. Fade to black.

---

## 🎬 Cinematic Post-Production Tips (CapCut / Premiere Pro)

1. **Digital Zooms:** Never use the browser's built-in `Ctrl +` zoom. Record at native 1440p, then use keyframes in your video editor to smoothly punch in 15-20% on specific charts to focus the viewer's eye.
2. **Cursor Highlighting:** Add a very subtle, semi-transparent halo around your mouse cursor during post-production so recruiters can track your movements instantly.
3. **Pacing:** If you stumble on a click, stop, pause for 3 seconds, and re-do the click. Cut out the dead space in post. Do not try to do it all in one perfect take.
