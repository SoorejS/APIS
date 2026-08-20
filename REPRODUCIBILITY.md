# APIS V2 — Research Experiment Reproducibility Guide
**Protocol Version:** APIS Research Spec v2.0-rc  
**Last Verified:** August 20, 2026

---

## 1. Environment & Dependencies

- **OS:** Windows 10/11 / Linux x86_64 / macOS Darwin
- **Python:** Python 3.11+ (Tested on Python 3.13.5)
- **Node.js:** Node 20.x+ / Next.js 16.x
- **Key Python Packages:** `fastapi`, `sqlalchemy`, `scipy`, `numpy`, `hdbscan`, `scikit-learn`, `pytest`, `httpx`

---

## 2. Dataset Cryptographic Integrity

- **Holdout A Manifest:** `backend/data/holdout_manifest.json`
- **SHA-256 Hash:** `aea267054e7e52e22ba691ad0f159b39e0c055cc3436b3fd85236a980749baaa`
- **Sample Counts:** Holdout A ($N=250$), Holdout B ($N=250$), Living Benchmark ($N=51$).

---

## 3. Reproduction Commands

```bash
# 1. Run full statistical audit and recomputation
python -m backend.services.audit_engine

# 2. Run one-click end-to-end experiment replication
python -m backend.experiments.reproduce_real_llm_experiment

# 3. Run complete multi-run, ablation, and human eval experiment
python -m backend.experiments.run_real_llm_experiment
```

---

## 4. Expected Outputs

- **Holdout A Pass Rate:** Baseline $35.6\%$ ($89/250$) $\rightarrow$ Winner $53.6\%$ ($134/250$) ($\Delta = +18.0\%$).
- **McNemar Chi-Square:** $\chi^2 = 31.738$, $p = 1.76 \times 10^{-8}$ (**Statistically Significant**).
- **95% Bootstrap Paired CI:** $[12.4\%, 23.6\%]$ percentage points improvement.
