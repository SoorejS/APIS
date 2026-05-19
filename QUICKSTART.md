# APIS Quickstart Guide

This guide walks you through setting up, verifying, and running the **APIS (Adaptive Prompt Intelligence System)** monorepo from scratch.

---

## 1. System Requirements & Prerequisites

*   **Python**: Version `3.10` to `3.13`
*   **Docker**: Docker Desktop (or equivalent engine) with Docker Compose installed.
*   **Operating System**: Windows / Linux / macOS (commands below are shown for Windows/PowerShell and general bash shells).

---

## 2. Infrastructure Initialization

Spin up PostgreSQL (persistence layer) and Redis (caching and job broker storage) using Docker Compose:

```bash
docker-compose up -d
```

Verify that the containers are healthy:
```bash
docker ps
```
You should see:
*   `apis-postgres` listening on port `5432`
*   `apis-redis` listening on port `6379`

---

## 3. Environment & Configuration

Copy the example environment file and configure variables:

```powershell
copy .env.example .env
```

Ensure `.env` contains the correct database connection strings:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/apis
REDIS_URL=redis://localhost:6379/0
# Add your Gemini API Key if you want to run live LLM iterations/evaluations:
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 4. Dependencies & Virtual Environment

Create a virtual environment and install all packages:

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Database Setup & Migrations

APIS uses Alembic to manage database migrations. Upgrade your local database schema to the latest head:

```bash
# If on Windows, ensure your virtual environment is active
alembic upgrade head
```

---

## 6. Seed Benchmark Datasets

Compile the $N=300$ complex query benchmark dataset (100 queries each for Customer Support, Coding Assistant, and Research Assistant):

```bash
python -m backend.experiments.datasets_generator
```

---

## 7. Verification & Tests

Validate that the entire PromptOps suite passes unit and integration checks:

```bash
pytest
```
*Expected Output: `25 passed in < 10 seconds`.*

---

## 8. Run the Interactive Demos

### A. The 2-Minute Closed-Loop CLI Demo
See the complete end-to-end adaptive optimization loop in action (Ingestion $\rightarrow$ Signal Engine $\rightarrow$ Optimization $\rightarrow$ Normalization $\rightarrow$ Ensemble Evaluation $\rightarrow$ Promotion):

```bash
python run_demo.py
```

### B. Interactive Double-Blind Human Study CLI
Launch the interactive human rating tool to grade randomized Baseline vs Adaptive outputs (N=20 queries):

```bash
python -m backend.experiments.human_eval --interactive
```

---

## 9. Launch the Backend API Dev Server

Start the FastAPI application:

```bash
uvicorn backend.main:app --reload --port 8000
```

Verify that the interactive Swagger API documentation is available at:
$$\text{Swagger UI Endpoint} \rightarrow \mathbf{\text{http://127.0.0.1:8000/docs}}$$
