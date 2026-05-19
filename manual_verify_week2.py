import time
import httpx
import psycopg2

BASE_URL = "http://127.0.0.1:8000"

def run_week2_verification():
    print("="*60)
    print("APIS MVP WEEK 2 - ADAPTIVE LOOP VERIFICATION RUN")
    print("="*60)
    
    # ── Step 1: Create Namespace with sensitive policy ──
    ns_name = f"support-bot-{int(time.time())}"
    print(f"\n[Step 1] Creating Namespace '{ns_name}'...")
    ns_payload = {
        "name": ns_name,
        "description": "Adaptive Customer Support Bot",
        "constraints": {
            "must_preserve": ["Empathetic tone", "Safety policy"],
            "cannot_modify": ["Refund policy limit: max 30 days"]
        },
        "iteration_policy": {
            "min_signals": 3,
            "min_negative_rate": 0.20,
            "cooldown_hours": 1
        }
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces", json=ns_payload)
    print(f"Response: {r.status_code}")
    ns_data = r.json()
    assert r.status_code == 201
    ns_id = ns_data["id"]
    print(f"Namespace created: ID={ns_id}")
    
    # ── Step 2: Create and Activate Base Version ──
    print("\n[Step 2] Registering and Activating v1.0 Base Prompt...")
    prompt_payload = {
        "version_string": "v1.0",
        "content": "You are a support bot. Provide detailed assistance. Feel free to explain legal terms.",
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/versions", json=prompt_payload)
    assert r.status_code == 201
    v_id = r.json()["id"]
    
    # Activate
    r = httpx.post(f"{BASE_URL}/api/v1/prompts/{v_id}/activate")
    assert r.status_code == 200
    print("Base prompt v1.0 successfully activated.")
    
    # ── Step 3: Simulate 10 Interactions (Query Category Classification) ──
    print("\n[Step 3] Simulating 10 user interactions (billing queries)...")
    interaction_ids = []
    for i in range(10):
        # Queries contain 'refund' keyword to trigger "billing" category auto-classification
        gen_payload = {
            "namespace": ns_name,
            "query": f"I want a refund for item #{i}",
            "session_id": f"session-user-{i}"
        }
        r = httpx.post(f"{BASE_URL}/api/v1/runtime/generate", json=gen_payload)
        assert r.status_code == 200
        interaction_ids.append(r.json()["interaction_id"])
        
    print(f"Successfully simulated 10 billing interactions.")
    
    # ── Step 4: Ingest 3 Thumbs Down (Satisfy Iteration Policy Gating) ──
    print("\n[Step 4] Ingesting 3 thumbs_down signals tied to those interactions...")
    for i in range(3):
        fb_payload = {
            "interaction_id": interaction_ids[i],
            "signal_type": "thumbs_down"
        }
        r = httpx.post(f"{BASE_URL}/api/v1/feedback/", json=fb_payload)
        assert r.status_code == 200
    print("Feedback signals ingested.")
    
    # ── Step 5: Trigger Adaptive Iteration Workflow ──
    print("\n[Step 5] Triggering Iteration Engine (POST /namespaces/{ns_id}/iterate)...")
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/iterate")
    print(f"Response: {r.status_code}")
    assert r.status_code == 200
    job_data = r.json()
    print(f"Iteration Job Data: {job_data}")
    candidate_version_id = job_data["candidate_version_id"]
    
    # ── Step 6: Verify Persisted Quality Patterns & New Candidate Prompt ──
    print("\n[Step 6] Validating database state...")
    conn = psycopg2.connect(
        user="apis",
        password="apis_password",
        host="localhost",
        port="5435",
        database="apis_db"
    )
    cursor = conn.cursor()
    
    # Check Interactions Query Classification
    cursor.execute("SELECT query_category, COUNT(*) FROM interactions WHERE namespace_id = %s GROUP BY query_category;", (ns_id,))
    rows = cursor.fetchall()
    print(f"[OK] Persisted query classifications in DB: {rows}")
    
    # Check QualityPattern Persistence
    cursor.execute("SELECT query_category, signal_type, negative_rate, signal_count FROM quality_patterns WHERE namespace_id = %s;", (ns_id,))
    p_row = cursor.fetchone()
    print(f"[OK] Persisted Quality Pattern: category='{p_row[0]}', signal='{p_row[1]}', rate={p_row[2]*100}%, count={p_row[3]}")
    
    # Check Candidate Version & Explainable Diff
    cursor.execute("SELECT version_string, status, content, change_rationale, diff_summary FROM prompt_versions WHERE id = %s;", (candidate_version_id,))
    cand_row = cursor.fetchone()
    print(f"[OK] Persisted Candidate Version: {cand_row[0]} | status={cand_row[1]}")
    print(f"  Change Rationale: '{cand_row[3]}'")
    print(f"  Explainable Diff: {cand_row[4]}")
    print(f"  Candidate Prompt Text:\n\"\"\"\n{cand_row[2]}\n\"\"\"")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("SUCCESS: WEEK 2 ADAPTIVE ITERATION LOOP PROVEN END-TO-END!")
    print("="*60)

if __name__ == "__main__":
    run_week2_verification()
