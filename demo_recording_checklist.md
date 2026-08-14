# APIS Recording Checklist

To ensure your demo looks like a premium startup launch and not a quick Zoom recording, verify these settings before hitting record.

## 1. System Cleanup
- [ ] **Hide Desktop Icons:** Right-click desktop -> View -> Uncheck "Show desktop icons" (Windows) or use a tool like Hidden (Mac).
- [ ] **Do Not Disturb:** Turn on Do Not Disturb mode so Slack/Discord notifications don't ruin a take.
- [ ] **Clean Bookmarks Bar:** Hide your browser bookmarks bar (`Ctrl+Shift+B` or `Cmd+Shift+B`).
- [ ] **Close Tabs:** Close all browser tabs except the APIS dashboard and the GitHub repo.

## 2. Browser & Visual Settings
- [ ] **Dark Mode:** Ensure your OS and browser are forced into Dark Mode. It makes charts pop and looks more technical.
- [ ] **Browser Zoom:** Set the browser zoom to **110% or 125%**. 100% is often too small for mobile viewers on LinkedIn/Twitter.
- [ ] **Full Screen:** Run the browser in full screen (`F11`) to hide the URL bar, or at least maximize the window cleanly.

## 3. OBS / Recording Settings
- [ ] **Resolution:** Set Base Canvas and Output Resolution to **2560x1440 (1440p)** if your monitor supports it, or **1920x1080 (1080p)** minimum.
- [ ] **Framerate:** Set FPS to **60**. This makes the Recharts animations and hover tooltips look buttery smooth.
- [ ] **Bitrate:** Set Video Bitrate to at least **15,000 Kbps** to prevent the text from looking blurry during transitions.
- [ ] **Format:** Record in `.mkv` (to prevent corruption if it crashes) and remux to `.mp4` afterward via OBS (File -> Remux Recordings).

## 4. Audio (If Recording Live)
- [ ] **Mic Check:** Ensure OBS is picking up your good microphone, not your webcam mic.
- [ ] **Filters:** Add a basic "Noise Suppression" (RNNoise) filter in OBS to kill background hums and keyboard clacks.
- [ ] *Alternative:* Record the screen silently first using the `demo_storyboard.md`, then record the audio voiceover separately in CapCut/Premiere and sync them up. This is usually much easier and sounds vastly more professional.

## 5. Seed Data Pre-Flight
- [ ] Run `python backend/scripts/seed_demo_data.py` right before recording so the charts show fresh, active data for "Today".
- [ ] Ensure the Next.js server is running without any dev-mode compilation errors hanging in the terminal.
