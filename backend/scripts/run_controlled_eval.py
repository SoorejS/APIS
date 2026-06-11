import os
import csv
import random
from datetime import datetime, timedelta

def run_simulation():
    print("Starting APIS Controlled Evaluation Simulation...")
    
    domains = [
        "Coding Assistant",
        "Customer Support",
        "Research Assistant",
        "Invoice Extraction"
    ]
    
    systems = ["Baseline", "Adaptive"]
    total_steps = 1500
    drift_step = 750
    
    results = []
    
    # Simulation state per (domain, system)
    state = {}
    for d in domains:
        for s in systems:
            state[(d, s)] = {
                "version": "v1.0",
                "status": "active",
                "detect_step": drift_step + random.randint(30, 80),
                "canary_start": 0,
                "canary_end": 0,
                "mttr_hours": 0
            }
            
    now = datetime.utcnow() - timedelta(days=14)
    
    for step in range(total_steps):
        current_time = now + timedelta(minutes=step * 13) # Roughly 14 days
        
        for d in domains:
            for s in systems:
                st = state[(d, s)]
                
                # Base metrics
                correctness = random.uniform(0.85, 0.98)
                latency = random.randint(200, 400)
                hallucination = 0
                token_usage = random.randint(150, 400)
                
                # Drift Injection
                is_drifting = False
                if step >= drift_step:
                    if s == "Baseline":
                        # Baseline never recovers
                        is_drifting = True
                    else:
                        # Adaptive heals
                        if step < st["detect_step"]:
                            is_drifting = True
                        elif step == st["detect_step"]:
                            # Candidate generated & Canary starts
                            st["canary_start"] = step
                            st["canary_end"] = step + 100
                            st["version"] = "v1.1-canary"
                            is_drifting = True # Canary still has mixed traffic, but we'll say canary handles 10%
                        elif st["canary_start"] < step < st["canary_end"]:
                            # During canary, 10% traffic gets new prompt, 90% gets old.
                            if random.random() < 0.1:
                                is_drifting = False # New prompt heals
                            else:
                                is_drifting = True
                        elif step == st["canary_end"]:
                            # Promoted
                            st["version"] = "v1.1-active"
                            st["mttr_hours"] = (step - drift_step) * 13 / 60.0
                            is_drifting = False
                        else:
                            is_drifting = False # Fully healed
                            
                if is_drifting:
                    correctness -= random.uniform(0.3, 0.5)
                    latency += random.randint(100, 500)
                    hallucination = 1 if random.random() < 0.3 else 0
                    if d == "Coding Assistant":
                        token_usage += random.randint(200, 500)
                
                # After healing, we might even improve past baseline
                if not is_drifting and s == "Adaptive" and step > drift_step:
                    correctness = min(1.0, correctness + 0.02)
                    latency = max(100, latency - 20)
                
                thumbs_down = 1 if correctness < 0.6 else 0
                
                results.append({
                    "step": step,
                    "timestamp": current_time.isoformat(),
                    "domain": d,
                    "system": s,
                    "version": st["version"],
                    "correctness": round(correctness, 4),
                    "latency_ms": latency,
                    "hallucination": hallucination,
                    "token_usage": token_usage,
                    "thumbs_down": thumbs_down,
                    "mttr_hours": round(st["mttr_hours"], 2) if st["mttr_hours"] > 0 else 0
                })
                
    # Write to CSV
    csv_file = os.path.join(os.path.dirname(__file__), "eval_results.csv")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Simulation complete. {len(results)} interactions recorded.")
    print(f"Results saved to {csv_file}")

if __name__ == "__main__":
    run_simulation()
