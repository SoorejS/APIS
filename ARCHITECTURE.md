# APIS: Flagship Architecture & Diagrams

This document contains the architectural diagrams for the APIS (Adaptive Prompt Infrastructure System) project. To ensure transparency and trust with senior engineers, we favor absolute honesty regarding system maturity over hype.

**Architecture Maturity Legend:**
- 🟢 **Implemented:** Live in production / MVP codebase.
- 🟡 **Simulated / Validated:** Concept mathematically proven via the Phase 7 Deterministic Simulator, but not yet running as a live asynchronous daemon.
- 🔵 **Roadmap:** Aspirational components slated for future versions.

---

## 1. High-Level System Architecture

### Explanation
This diagram answers "What is APIS?" at a glance. It illustrates how client traffic flows through the implemented APIS Gateway, routing to various LLM providers, while telemetry is captured in PostgreSQL. The Adaptive Engine (simulated in v1) handles canary deployments, candidate generation, and drift detection.

### Design Rationale
The goal is to show APIS as an *infrastructure layer* sitting securely between the client and the LLM providers, clearly distinguishing the live runtime vs the simulated orchestration loops.

### Mermaid Source
```mermaid
graph TD
    classDef client fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef apis fill:#e0f2fe,stroke:#0284c7,stroke-width:3px;
    classDef provider fill:#f3e8ff,stroke:#9333ea,stroke-width:2px;
    classDef simulated fill:#fef08a,stroke:#ca8a04,stroke-width:2px,stroke-dasharray: 5 5;
    classDef db fill:#fef3c7,stroke:#d97706,stroke-width:2px;

    Client[Client Applications]:::client -->|API Request| Gateway[🟢 APIS Gateway / Router]:::apis
    
    Gateway -->|Forward| LLMs[🟢 LLM Providers]:::provider
    LLMs -->|Response| Gateway
    Gateway -->|Response + Telemetry| Client
    
    Gateway -.->|Async Telemetry Logs| DB[(🟢 PostgreSQL DB)]:::db
    
    subgraph "APIS Adaptive Engine"
        DB -.->|Read Metrics| Worker[🟡 Background Worker]:::simulated
        Worker -.->|Trigger Drift Alert| Generator[🟡 Candidate Generator]:::simulated
        Worker -.->|Manage State| Canary[🟡 Auto-Promotion Manager]:::simulated
        Generator -.->|Write Candidate| DB
        Canary -.->|Update Route Rules| DB
    end
    
    DB -.->|Pull Config| Gateway
```

---

## 2. Runtime Execution Flow

### Explanation
This diagram details the exact request path when a user hits the APIS endpoint. It proves backend depth by showing the router logic, fallback chains, and how telemetry is captured.

### Design Rationale
This maps to the FastAPI routing logic implemented in the backend, focusing on the resilient execution paths (fallback chains and fractional hashing).

### Mermaid Source
```mermaid
flowchart TD
    classDef startend fill:#1e293b,stroke:#fff,color:#fff;
    classDef decision fill:#fef08a,stroke:#ca8a04;
    classDef action fill:#e0e7ff,stroke:#4f46e5;
    
    Start((Incoming API Req)):::startend --> Resolve[🟢 Resolve Namespace & Rules]:::action
    Resolve --> CheckCanary{🟢 Is Canary Active?}:::decision
    
    CheckCanary -- Yes --> Hash[🟢 Hash UserID % 100]:::action
    Hash -- "< Rollout %" --> PickCanary[🟢 Load Canary Prompt]:::action
    Hash -- ">= Rollout %" --> PickActive[🟢 Load Active Prompt]:::action
    CheckCanary -- No --> PickActive
    
    PickCanary --> ProviderSelect[🟢 Select Primary Provider]:::action
    PickActive --> ProviderSelect
    
    ProviderSelect --> CallLLM[🟢 Execute LLM Call]:::action
    CallLLM --> SuccessCheck{🟢 Success?}:::decision
    
    SuccessCheck -- No --> Fallback[🟢 Execute Provider Fallback]:::action
    Fallback --> CallLLM
    
    SuccessCheck -- Yes --> Parse[🟢 Parse Output & Check Constraints]:::action
    Parse --> AsyncLog[🟢 Fire Background Task:<br/>Save Interaction to DB]:::action
    AsyncLog --> End((Return Response)):::startend
```

---

## 3. Prompt Evolution Lifecycle

### Explanation
This diagram explains the state machine of a prompt. It shows how user feedback translates into a new prompt version, goes through offline evaluation, hits production via a canary, and is finally promoted.

### Design Rationale
The state transitions represent strict enumerations enforced in the Postgres schema today, while the actual LLM-as-a-judge automated evaluation is clearly marked as roadmap.

### Mermaid Source
```mermaid
stateDiagram-v2
    direction LR
    
    state "🟢 Production Feedback" as Feedback
    state "🟢 Draft / Candidate" as Draft
    state "🔵 Offline LLM-as-Judge Eval" as Eval
    state "🟢 Active Canary (10%)" as Canary
    state "🟢 Fully Promoted (Active)" as Active
    state "🟢 Rejected / Rolled Back" as Rejected

    [*] --> Feedback: Collect Signal
    Feedback --> Draft: 🟡 Background Generator
    Draft --> Eval: 🔵 Automated Test
    
    Eval --> Rejected: Failed Benchmarks
    Eval --> Canary: Passed Benchmarks
    
    Canary --> Canary: 🔵 Auto-Monitor 1h
    Canary --> Rejected: 🟢 Latency/Error Spike (DB Enforced)
    Canary --> Active: 🟢 Metrics Stable (DB Enforced)
    
    Active --> [*]
```

---

## 4. Canary Safety System

### Explanation
This diagram highlights the gradual rollout and safety nets. It proves to infrastructure engineers that APIS treats prompts with the same rigor as compiled backend binaries.

### Design Rationale
It distinguishes the *implemented* fractional routing and rollback execution from the *roadmap* automated scheduler that promotes traffic percentages chronologically.

### Mermaid Source
```mermaid
graph LR
    classDef version fill:#f8fafc,stroke:#94a3b8;
    classDef traffic fill:#bfdbfe,stroke:#3b82f6;
    classDef rollback fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
    classDef success fill:#dcfce3,stroke:#22c55e,stroke-width:2px;

    V1[🟢 v1.0 Active<br/>90% Traffic]:::version
    V2[🟢 v1.1 Candidate<br/>10% Traffic]:::traffic
    
    V1 --- Monitor((🟡 Monitor Error Rate))
    V2 --- Monitor
    
    Monitor -->|🔵 Stable 1h<br/>(Cron Scheduler)| T25[🟢 v1.1 Canary 25%]:::traffic
    Monitor -->|🟢 Latency Spike!| RB[🟢 Automatic Rollback<br/>v1.0 = 100%]:::rollback
    
    T25 -->|🔵 Stable 1h| T50[🟢 v1.1 Canary 50%]:::traffic
    T50 -->|🔵 Stable 1h| Full[🟢 v1.1 Promoted<br/>100% Traffic]:::success
```

---

## 5. Proposed Drift Detection Architecture (Validated via Simulation)

### Explanation
This details the proposed observability and anomaly detection pipeline. It shows how the system notices "hidden degradation" (like creeping verbosity or hallucinations) before users complain.

### Design Rationale
Since the active 5-minute cron job is heavily simulated in the current MVP (via Phase 7 evaluation scripts), this diagram is labeled as a validated proposal rather than a live production component.

### Mermaid Source
```mermaid
sequenceDiagram
    participant DB as 🟢 Postgres (Telemetry)
    participant Worker as 🟡 Drift Detection Cron
    participant Engine as 🟡 Adaptive Engine
    participant UI as 🟢 Dashboard Alerting

    loop Every 5 Minutes
        Worker->>DB: Query Last 1000 Interactions
        Worker->>Worker: Calculate Hallucination & Thumbs Down %
        
        opt Metric > Baseline + 3σ (Threshold Breach)
            Worker->>UI: Dispatch Drift Alert (Critical)
            Worker->>Engine: Trigger Auto-Heal Loop
            Engine->>DB: Fetch specific failing inputs
            Engine->>Engine: LLM: Generate Candidate Prompt targeting failures
            Engine->>DB: Save new Candidate Version
            Engine->>Engine: Trigger Canary Rollout
        end
    end
```

---

## 6. Evaluation Framework

### Explanation
This diagram validates the research credibility of Phase 7. It visually explains the methodology of the 12,000-interaction simulation, the injected drift event, and how the Baseline and Adaptive systems diverged.

### Design Rationale
By showing two parallel timelines diverging after a specific event ("Drift Injected"), it instantly communicates the rigorous A/B testing methodology used to prove the system's mathematical viability.

### Mermaid Source
```mermaid
flowchart TD
    classDef setup fill:#f1f5f9,stroke:#64748b;
    classDef drift fill:#fef08a,stroke:#eab308,stroke-width:2px;
    classDef base fill:#fee2e2,stroke:#ef4444;
    classDef adapt fill:#dcfce3,stroke:#22c55e;

    Setup[🟢 Simulate 12,000 Interactions<br/>Across 4 Domains]:::setup --> Parallel
    
    subgraph Parallel Simulation
        direction LR
        S1[🟢 Static Baseline System]
        S2[🟢 APIS Adaptive System]
    end
    
    Parallel --> Step750((🟢 Step 750:<br/>Inject Deterministic Drift)):::drift
    
    Step750 --> BaseDegrade[🟢 Baseline correctness<br/>drops to 52% and stays dead]:::base
    Step750 --> AdaptHeal[🟢 APIS detects drift,<br/>rolls out canary, heals to 98%]:::adapt
    
    BaseDegrade --> Report[🟢 Generate CSV & Markdown Eval Report]
    AdaptHeal --> Report
```

---

## 🎨 Exportable SVG/Figma-Ready Plan

To convert these Mermaid diagrams into best-in-class assets for your repository or slide decks:

1. **GitHub README:** Paste the raw ` ```mermaid ` blocks directly into `README.md`. GitHub natively renders them in dark/light mode matching the user's OS preference.
2. **Figma / Slide Decks:** 
   - Open the [Mermaid Live Editor](https://mermaid.live).
   - Paste the code blocks above.
   - Click **Actions -> Export SVG**.
   - Drag the SVG into Figma. Because it's an SVG, all shapes and text will be fully editable vectors. You can then apply your specific APIS brand colors (e.g., your Next.js dashboard's exact HSL values) to make them look identical to the UI.
