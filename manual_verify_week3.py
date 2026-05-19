import time
import httpx
import psycopg2

BASE_URL = "http://127.0.0.1:8000"

def run_week3_verification():
    print("="*80)
    print("APIS MVP WEEK 3 - GATED OFFLINE EVALUATION ENGINE VERIFICATION RUN")
    print("="*80)
    
    # ── Step 1: Create Namespace with sensitive policy ──
    ns_name = f"support-bot-week3-{int(time.time())}"
    print(f"\n[Step 1] Creating Namespace '{ns_name}'...")
    ns_payload = {
        "name": ns_name,
        "description": "Gated Production Customer Bot",
        "constraints": {
            "must_preserve": ["Professional tone"],
            "cannot_modify": ["Max 30 day refund limit"]
        },
        "iteration_policy": {
            "min_signals": 3,
            "min_negative_rate": 0.20,
            "cooldown_hours": 1
        }
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces", json=ns_payload)
    assert r.status_code == 201
    ns_id = r.json()["id"]
    print(f"Namespace created: ID={ns_id}")
    
    # ── Step 2: Register & Activate v1.0 Base Prompt ──
    print("\n[Step 2] Registering and Activating v1.0 Base Prompt...")
    prompt_payload = {
        "version_string": "v1.0",
        "content": "You are a customer assistant. Help people solve issues.",
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/versions", json=prompt_payload)
    assert r.status_code == 201
    v_id = r.json()["id"]
    
    r = httpx.post(f"{BASE_URL}/api/v1/prompts/{v_id}/activate")
    assert r.status_code == 200
    print("Base prompt v1.0 successfully activated.")
    
    # ── Step 3: Simulate 10 Billing Interactions & Ingest 3 Thumbs Down ──
    print("\n[Step 3] Simulating 10 user interactions & 3 thumbs_down signals...")
    interaction_ids = []
    for i in range(10):
        gen_payload = {
            "namespace": ns_name,
            "query": f"Need refund for purchase order #{i}",
            "session_id": f"sess-week3-{i}"
        }
        r = httpx.post(f"{BASE_URL}/api/v1/runtime/generate", json=gen_payload)
        assert r.status_code == 200
        interaction_ids.append(r.json()["interaction_id"])
        
    for i in range(3):
        fb_payload = {
            "interaction_id": interaction_ids[i],
            "signal_type": "thumbs_down"
        }
        r = httpx.post(f"{BASE_URL}/api/v1/feedback/", json=fb_payload)
        assert r.status_code == 200
    print("Ingested feedback signals and satisfied PolicyEngine gating conditions.")
    
    # ── Step 4: Run Adaptive Loop to generate v1.1-candidate ──
    print("\n[Step 4] Running Adaptive Iteration Workflow to generate candidate prompt...")
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/iterate")
    assert r.status_code == 200
    candidate_version_id = r.json()["candidate_version_id"]
    print(f"Adaptive Loop finished. Created Candidate Version ID: {candidate_version_id}")
    
    # Connect to PostgreSQL to query state
    conn = psycopg2.connect(
        user="apis",
        password="apis_password",
        host="localhost",
        port="5435",
        database="apis_db"
    )
    cursor = conn.cursor()
    
    # ── Step 5: Test Gated Rejection (Run A: Simulated Regression) ──
    print("\n[Step 5] Triggering Evaluation Run A: Gated Regression Path (billing +18%, coding -4%)...")
    eval_payload = {
        "candidate_version_id": candidate_version_id,
        "simulate_regression": True
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/evaluations/run", json=eval_payload)
    print(f"Response: {r.status_code}")
    assert r.status_code == 201
    run_data_a = r.json()
    print(f"Run A Finished! Overall Active: {run_data_a['overall_active_score']} | Candidate: {run_data_a['overall_candidate_score']}")
    print(f"Category scores showing regressions: {run_data_a['category_scores']}")
    print(f"--> Gating Decision: {run_data_a['decision'].upper()}")
    
    # Verify DB: versions state-machine must lock active base, reject candidate
    cursor.execute("SELECT version_string, status FROM prompt_versions WHERE id IN (%s, %s);", (v_id, candidate_version_id))
    versions_state_a = cursor.fetchall()
    print(f"[OK] Database Verification A: {versions_state_a}")
    for ver_str, status in versions_state_a:
        if ver_str == "v1.0":
            assert status == "active", "Active base version should NOT be archived!"
        elif "candidate" in ver_str:
            assert status == "rejected", "Candidate must be marked as rejected!"
            
    # ── Step 6: Test Gated Promotion (Run B: Clean Promotion Path) ──
    print("\n[Step 6] Registering a fresh v1.2-candidate version to test success path...")
    fresh_candidate_payload = {
        "version_string": "v1.2-candidate",
        "content": "You are a professional assistant.\n## OPERATIONAL GUIDELINES:\n- Help users solve queries concisely.",
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/versions", json=fresh_candidate_payload)
    assert r.status_code == 201
    fresh_candidate_id = r.json()["id"]
    
    print("\n[Step 7] Triggering Evaluation Run B: Clean Success Path (overall improvement, no regressions)...")
    eval_payload_b = {
        "candidate_version_id": fresh_candidate_id,
        "simulate_regression": False
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/evaluations/run", json=eval_payload_b)
    print(f"Response: {r.status_code}")
    assert r.status_code == 201
    run_data_b = r.json()
    print(f"Run B Finished! Overall Active: {run_data_b['overall_active_score']} | Candidate: {run_data_b['overall_candidate_score']}")
    print(f"Category scores showing improvements: {run_data_b['category_scores']}")
    print(f"--> Gating Decision: {run_data_b['decision'].upper()}")
    
    # Verify DB: base should be archived, fresh_candidate should be promoted to ACTIVE
    cursor.execute("SELECT version_string, status FROM prompt_versions WHERE id IN (%s, %s);", (v_id, fresh_candidate_id))
    versions_state_b = cursor.fetchall()
    print(f"[OK] Database Verification B: {versions_state_b}")
    for ver_str, status in versions_state_b:
        if ver_str == "v1.0":
            assert status == "archived", "Original base version MUST be archived!"
        elif ver_str == "v1.2-candidate":
            assert status == "active", "Promoted candidate MUST be marked active!"
            
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("SUCCESS: WEEK 3 GATED OFFLINE EVALUATION ENGINE PROVEN END-TO-END!")
    print("="*80)

if __name__ == "__main__":
    run_week3_verification()
