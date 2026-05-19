# APIS Architecture Specification

This document provides a comprehensive technical overview of the **APIS (Adaptive Prompt Intelligence System)** architecture, outlining how the dynamic PromptOps lifecycle operates end-to-end.

---

## 1. System Topology Overview

APIS is designed around a decoupled, state-machine architecture that splits the hot path (user query execution) from the cold path (feedback ingestion, pattern analysis, and automated prompt iteration).

```mermaid
flowchart TD
    subgraph Hot Path (Runtime Execution)
        Client([User Client]) -->|1. Generate request| API[Runtime Endpoint /generate]
        API -->|2. Get active version| DB[(PostgreSQL Store)]
        API -->|3. Compile layers| Compiler[PromptCompilerService]
        Compiler -->|4. Request completion| LLM[LLM Provider - Gemini]
        LLM -->|5. Return response & interaction_id| API
        API -->|6. Send back to user| Client
    end

    subgraph Cold Path (Continuous Optimization)
        Client -->|7. Thumbs down signal| FeedbackAPI[Feedback Endpoint /feedback]
        FeedbackAPI -->|8. Store feedback| DB
        
        DB -->|9. Pull records| SigEngine[SignalEngine]
        SigEngine -->|10. Classify queries| Classifier[QueryClassifier]
        SigEngine -->|11. Evaluate policy rules| PolicyEngine[ShouldIterate]
        
        PolicyEngine -->|12. Trigger optimization| IterEngine[IterationEngine]
        IterEngine -->|13. Structurally format| Normalizer[PromptNormalizerService]
        Normalizer -->|14. Zero-regression suite| Evaluator[EvaluatorService]
        
        Evaluator -->|15. Validate metrics| Gating{Quality Gate}
        Gating -->|Promote| DB
        Gating -->|Reject & Log| FailureMem[FailureMemoryService]
        FailureMem -->|Inject avoidance context| IterEngine
    end
```

---

## 2. Core Architectural Components

### 2.1. The Hot Path: Runtime & Compilation

*   **`Runtime API (/generate)`**: Ingests user inputs, locates the current `ACTIVE` prompt version for the specified namespace in PostgreSQL, compiles the effective prompt, calls the Gemini model, logs the raw interaction, and returns the response alongside a unique `interaction_id`.
*   **`PromptCompilerService`**: Merges structural elements to construct a unified system prompt:
    $$\text{Effective Prompt} = \text{Base System Instructions} + \text{Constraints Layer} + \text{Runtime Context}$$
    This guarantees constraints are never modified by the iteration layer and prevents prompt injection or structural degradation.

### 2.2. The Feedback Loop: Signal Engine & Policy

*   **`Feedback API (/feedback)`**: Associates user signals (e.g., thumbs_up, thumbs_down, too_long) with specific `interaction_id` keys in PostgreSQL.
*   **`SignalEngine`**: Processes a rolling window of recent interactions and signals. It calculates the negative feedback rate per query category:
    $$\text{Negative Rate} = \frac{\text{Negative Signal Count}}{\text{Total Interactions in Window}}$$
*   **`QueryClassifier`**: Categorizes user queries (e.g., `billing`, `legal`, `coding`, `general`) to isolate prompt performance metrics per domain.
*   **`PolicyEngine (ShouldIterate)`**: Evaluates whether a namespace should undergo optimization. Rules check if:
    *   The total number of category signals exceeds a minimum threshold (e.g., $N \ge 50$).
    *   The negative signal rate exceeds the threshold (e.g., $\ge 30\%$).
    *   The namespace is outside its cooldown window (e.g., 24 hours since the last promotion).

### 2.3. The Iteration Loop: Generation & Gating

*   **`IterationEngine`**: Orchestrates optimization. It pulls negative feedback patterns and recent user queries for the degraded category, and queries Gemini to generate a candidate prompt rewrite targeting the reported issues.
*   **`PromptNormalizerService`**: Parses and aligns candidate prompt structures. It deduplicates redundant rules, ensures strict Markdown formatting, and enforces system length boundaries to prevent prompt bloat.
*   **`EvaluatorService`**: Performs offline testing. It compiles a benchmark suite of historical queries and runs the candidate version against the active baseline using a **Multi-Judge Ensemble** (Strict Compliance, Technical Utility, and Clarity & Conciseness judges).
*   **`FailureMemoryService`**: Acts as a safety net. If a candidate is rejected during offline evaluation due to category regressions, the attempted fix and failure reason are logged to the database and injected directly into the next candidate generation iteration to prevent repeating errors.

---

## 3. Database Schema Specification

APIS relies on a PostgreSQL schema to coordinate state transitions:

| Table Name | Description | Key Relationships |
| :--- | :--- | :--- |
| **`prompt_namespaces`** | Isolates system domains (e.g., support, coding). Stores active constraints and iteration policies. | One-to-Many with `prompt_versions`, `interactions`, `quality_patterns`. |
| **`prompt_versions`** | Immutable log of all system prompt versions (`active`, `candidate`, `rejected`). | Many-to-One with `prompt_namespaces`. |
| **`interactions`** | Database of all production queries, outputs, latencies, and category labels. | Many-to-One with `prompt_versions`. |
| **`feedback_signals`** | Logs user interactions (thumbs up/down). | Many-to-One with `interactions`. |
| **`quality_patterns`** | Aggregated feedback metrics per category. Used to trigger iteration. | Many-to-One with `prompt_namespaces`. |
| **`evaluation_runs`** | Test runs comparing baseline vs candidate prompt performance. | References active and candidate `prompt_versions`. |
| **`failure_memories`** | Persistent history of rejected candidate optimizations. | Many-to-One with `prompt_namespaces`. |
