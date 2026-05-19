import time
import httpx
import psycopg2

BASE_URL = "http://127.0.0.1:8000"

def run_verification():
    print("="*60)
    print("APIS MVP WEEK 1 - SYSTEM VERIFICATION RUN")
    print("="*60)
    
    # ── Step 1: Health Check ──
    print("\n[Step 1] Checking API Health...")
    r = httpx.get(f"{BASE_URL}/health")
    print(f"Response: {r.status_code} | {r.json()}")
    assert r.status_code == 200
    
    # ── Step 2: Create Namespace ──
    ns_name = f"support-agent-{int(time.time())}"
    print(f"\n[Step 2] Creating Namespace '{ns_name}'...")
    ns_payload = {
        "name": ns_name,
        "description": "Customer support AI agent",
        "constraints": {
            "must_preserve": ["Empathetic tone", "Safety policy"],
            "cannot_modify": ["Refund policy: max 30 days"]
        },
        "iteration_policy": {
            "min_signals": 50,
            "min_negative_rate": 0.35,
            "cooldown_hours": 24
        }
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces", json=ns_payload)
    print(f"Response: {r.status_code}")
    ns_data = r.json()
    print(f"Namespace Data: {ns_data}")
    assert r.status_code == 201
    ns_id = ns_data["id"]
    
    # ── Step 3: Create Prompt Version ──
    print("\n[Step 3] Creating Prompt Version 'v1.0'...")
    prompt_payload = {
        "version_string": "v1.0",
        "content": "You are a customer support agent. Help users resolve their queries.",
        "change_rationale": "Initial base prompt release"
    }
    r = httpx.post(f"{BASE_URL}/api/v1/namespaces/{ns_id}/versions", json=prompt_payload)
    print(f"Response: {r.status_code}")
    version_data = r.json()
    print(f"Version Data: {version_data}")
    assert r.status_code == 201
    version_id = version_data["id"]
    
    # ── Step 4: Activate Version ──
    print("\n[Step 4] Promoting version 'v1.0' to ACTIVE...")
    r = httpx.post(f"{BASE_URL}/api/v1/prompts/{version_id}/activate")
    print(f"Response: {r.status_code}")
    active_data = r.json()
    print(f"Active Version Data: {active_data}")
    assert r.status_code == 200
    assert active_data["status"] == "active"
    
    # ── Step 5: Call Runtime generate (Proxy LLM generate) ──
    print("\n[Step 5] Triggering Runtime generate (Requirement 1 & 4)...")
    gen_payload = {
        "namespace": ns_name,
        "query": "Can I get a refund for my order #999?",
        "session_id": "session-xyz-123",
        "context_variables": {
            "user_tier": "Premium",
            "country": "US"
        }
    }
    r = httpx.post(f"{BASE_URL}/api/v1/runtime/generate", json=gen_payload)
    print(f"Response: {r.status_code}")
    gen_data = r.json()
    print(f"Generate Output: {gen_data}")
    assert r.status_code == 200
    interaction_id = gen_data["interaction_id"]
    print(f"Generated Interaction ID: {interaction_id}")
    print(f"Runtime Latency (Gemini Provider): {gen_data['latency_ms']} ms")
    
    # ── Step 6: Submit Feedback Signal ──
    print("\n[Step 6] Submitting user Feedback signal 'thumbs_down'...")
    fb_payload = {
        "interaction_id": interaction_id,
        "signal_type": "thumbs_down"
    }
    r = httpx.post(f"{BASE_URL}/api/v1/feedback/", json=fb_payload)
    print(f"Response: {r.status_code}")
    fb_data = r.json()
    print(f"Feedback Ingestion Output: {fb_data}")
    assert r.status_code == 200
    signal_id = fb_data["signal_id"]
    
    # ── Step 7: Database Persistence Validation ──
    print("\n[Step 7] Validating persisted PostgreSQL records (Requirement 1)...")
    conn = psycopg2.connect(
        user="apis",
        password="apis_password",
        host="localhost",
        port="5435",
        database="apis_db"
    )
    cursor = conn.cursor()
    
    # Verify Namespace
    cursor.execute("SELECT name, constraints FROM prompt_namespaces WHERE name = %s;", (ns_name,))
    ns_row = cursor.fetchone()
    print(f"[OK] DB Verified Namespace: name={ns_row[0]}, constraints={ns_row[1]}")
    
    # Verify Prompt Version
    cursor.execute("SELECT version_string, status FROM prompt_versions WHERE id = %s;", (version_id,))
    ver_row = cursor.fetchone()
    print(f"[OK] DB Verified Version: version={ver_row[0]}, status={ver_row[1]}")
    
    # Verify Interaction
    cursor.execute("SELECT user_query, ai_response, latency_ms FROM interactions WHERE id = %s;", (interaction_id,))
    int_row = cursor.fetchone()
    print(f"[OK] DB Verified Interaction: query='{int_row[0]}', latency={int_row[2]}ms")
    print(f"  AI Response persisted: '{int_row[1]}'")
    
    # Verify Feedback Signal
    cursor.execute("SELECT signal_type FROM feedback_signals WHERE id = %s;", (signal_id,))
    sig_row = cursor.fetchone()
    print(f"[OK] DB Verified Feedback Signal: signal_type={sig_row[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("SUCCESS: WEEK 1 ENGINE CORE PERSISTED AND VERIFIED END-TO-END!")
    print("="*60)

if __name__ == "__main__":
    run_verification()
