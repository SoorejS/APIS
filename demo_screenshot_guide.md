# APIS Demo: Screenshot & Recording Assessment

## Page-by-Page Score

| Page | Visual Impact | Technical Credibility | Recruiter Appeal | Storytelling | Action Required |
|------|:---:|:---:|:---:|:---:|---|
| Overview | 7/10 | 8/10 | 8/10 | 7/10 | Minor: numbers were too low (fixed in seed) |
| Runtime | 7/10 | 9/10 | 7/10 | 6/10 | Good: charts need data volume to show shape |
| Prompts | 8/10 | 9/10 | 9/10 | 10/10 | **Best page. Show it prominently.** |
| Canary | 9/10 | 10/10 | 10/10 | 10/10 | **Hero page. Rollback history is killer.** |
| Drift | 8/10 | 9/10 | 8/10 | 9/10 | Fixed CartesianGrid crash. Now shows red. |
| Eval Proof | 9/10 | 10/10 | 10/10 | 10/10 | Fixed colors. "Drift Injected" line is money. |

---

## Priority 4 — Screenshot Capture Guide

### 1. Hero Screenshot (Overview)
- **URL:** `http://localhost:3000/`
- **What to capture:** Full page. All 6 metric cards visible. Charts showing 7-day ramp.
- **Zoom:** Browser at 100%.
- **Filter:** None (show all namespaces combined = largest numbers).
- **Key metric to ensure visible:** `Total Requests: 103,4xx` — this is your social proof number.

### 2. Runtime Screenshot
- **URL:** `http://localhost:3000/runtime`
- **What to capture:** The 4 KPI cards at top + at least 1 chart below.
- **Zoom:** Browser at 110%.
- **Filter:** No filter — show all providers so the chart has shape.
- **Key element:** Hover your mouse over the "Avg Latency" trendline so the tooltip shows a specific number.

### 3. Prompt Evolution Screenshot (BEST PAGE)
- **URL:** `http://localhost:3000/prompts`
- **What to capture:** Expand the `billing-agent` v1.2-candidate card to show the "Rollback Reason" text.
- **Zoom:** Browser at 100%.
- **Key element:** The green "v1.3 active" card + the red "v1.2-candidate rolled_back" card side by side tells the entire story visually.

### 4. Canary Screenshot (SECOND BEST)
- **URL:** `http://localhost:3000/canary`
- **What to capture:** The RolloutState progress bar showing "25% Canary" in amber, plus the Rollback History cards below showing the `+210ms latency regression` text.
- **Zoom:** Browser at 100%.
- **Filter:** Select `invoice-extractor` (10% canary) for the most dramatic "in progress" visual.

### 5. Drift Screenshot
- **URL:** `http://localhost:3000/drift`
- **What to capture:** The red "Critical" hallucination spike badge at top + the Area chart showing the upward spike.
- **Zoom:** 110% zoom on the critical alert card. The red color is your signal.
- **Key element:** The "8.4% hallucination rate" text in the alert description.

### 6. Evaluation Screenshot (STRONGEST PROOF)
- **URL:** `http://localhost:3000/results`
- **What to capture:** The 4 KPI cards (+48.1% Correctness, -95.7% Hallucination, 1.8h MTTR, 100% rollback) + the "Correctness Degradation & Auto-Healing" chart with the "Drift Injected" reference line.
- **Zoom:** Browser at 90% to show everything on one screen.
- **Key element:** The moment where the baseline flatlines after step 750 while the APIS line recovers — **this is the money shot of the entire project.**

---

## Priority 5 — Demo Readiness Assessment

### ✅ Demo Ready: YES (with caveats)
### ✅ GitHub Ready: YES
### ✅ Recruiter Ready: YES
### ✅ Portfolio Ready: YES

---

## Must Fix Before Recording

1. ✅ **DONE** — Re-seed data to 103k+ interactions (believable production volume)
2. ✅ **DONE** — Fix `hsl(var())` color bugs on Drift, Canary, Results pages (charts were all black)
3. ✅ **DONE** — Fix `CartesianGrid not defined` crash on Drift page
4. **TODO** — Refresh browser after seed completes and confirm "Total Requests" shows 103k+ on Overview

## Nice To Have (Skip For Now)

- More distinct chart colors per provider (minor visual upgrade)
- Animated counter on Overview KPI cards (cool but not worth the time)
- Mobile responsiveness pass (do this after you record)

## Safe To Ignore

- The `datetime.utcnow()` DeprecationWarning — it's a Python 3.12 warning, won't break anything
- The `collapsible="true"` warning (already fixed)
- The cross-origin webpack warning (dev-only, not visible in recording)

---

## Role-Specific Talking Points

| Role | Focus On | Phrase To Use |
|------|----------|---------------|
| AI Engineer | Drift detection + feedback loop | "Closed-loop prompt observability" |
| Backend Engineer | Fractional routing + SQLite/Postgres persistence + FastAPI | "Production-safe canary infrastructure" |
| Founding Engineer | Full-stack: FastAPI + Next.js + telemetry + eval framework | "I built the full stack from scratch" |
| SWE (Big Tech) | Evaluation framework rigor + 12k interaction simulation | "Research-grade controlled evaluation" |
