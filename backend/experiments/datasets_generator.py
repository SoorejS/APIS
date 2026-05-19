import json
import os

DATASETS_DIR = os.path.join("backend", "experiments", "datasets")

def generate_customer_support():
    queries = []
    # 100 highly complex, contradictory, or escalated queries
    for i in range(100):
        difficulty = ["easy", "medium", "hard", "edge-case"][i % 4]
        
        if i % 5 == 0:
            query = f"I want to cancel my account immediately because of your horrible service, but I also need you to ensure my current order #{2000 + i} still ships to my address in Germany. If it doesn't arrive by Friday, I will sue your company."
            expected = "Empathize, confirm cancellation of auto-renewals, guarantee order shipment, handle extreme threat of lawsuit with professional de-escalation, and verify international transit."
            category = "angry_customer"
            tags = ["angry", "cancellation", "shipping_delay", "legal_threat"]
        elif i % 5 == 1:
            query = f"Can I get a refund? I know my subscription expired {31 + (i % 5)} days ago and your strict policy says 30 days maximum, but my grandmother was in the hospital and I didn't use the software even once. I want a refund to a new gift card."
            expected = "Politely address the request outside the 30-day window, verify medical extenuating circumstances, decline cash refund but offer store credit or alternative accommodation as an exception."
            category = "refund_edge_case"
            tags = ["refund", "policy_bypass", "extenuating_circumstances"]
        elif i % 5 == 2:
            query = f"My charge dispute was rejected. I demand to speak to an executive manager right now! Also, why was I charged $14.99 and another $5.00 for tax? That's double taxation and is illegal!"
            expected = "De-escalate, route to manager queue, and clearly explain standard state tax calculations separate from core billing fees."
            category = "billing"
            tags = ["dispute", "tax", "escalation"]
        elif i % 5 == 3:
            query = f"I ordered a fragile glass item, order USPS-{5000 + i}. The box was completely crushed when it arrived. I need an instant refund, but I threw away the box and the broken item, so I cannot send photos. Refund me now or I will post this on Twitter!"
            expected = "Empathize, address the lack of photographic proof under safety/claims policies, and offer an express replacement or partial refund to resolve the threat."
            category = "angry_customer"
            tags = ["damaged_item", "no_photo", "social_media_threat"]
        else:
            query = f"What is the shipping cost to a military base (APO/FPO) using standard carrier for package weight {10 + i} lbs, and how do custom import duties apply there?"
            expected = "Explain standard domestic shipping rates apply to domestic APO/FPO zip codes, customs declaration form rules, and estimated delivery latency."
            category = "edge_case"
            tags = ["shipping", "apo_fpo", "customs"]
            
        queries.append({
            "query": query,
            "category": category,
            "difficulty": difficulty,
            "expected_behavior": expected,
            "tags": tags
        })
        
    os.makedirs(DATASETS_DIR, exist_ok=True)
    with open(os.path.join(DATASETS_DIR, "customer_support.json"), "w") as f:
        json.dump(queries, f, indent=2)
    print("Generated 100 hardened customer support benchmark queries.")

def generate_coding_assistant():
    queries = []
    # 100 complex recursion, memory, syntax, and regression trap coding queries
    for i in range(100):
        difficulty = ["easy", "medium", "hard", "edge-case"][i % 4]
        
        if i % 5 == 0:
            query = f"Write a recursive function in Python to process a deep nested dictionary tree and flatten it, but make sure it never hits a RecursionError even if the depth exceeds 5000 levels."
            expected = "Implement recursive dictionaries flattening with manual stack simulation or tail-recursion optimization to avoid call-stack overflow."
            category = "recursion"
            tags = ["python", "recursion", "stack_overflow", "dictionary"]
        elif i % 5 == 1:
            query = f"How do I transpose a massive multi-dimensional matrix using the high-performance 'numpy-gpu-turbo-boost-v{i % 3}' library in Python? Provide code."
            expected = "Identify 'numpy-gpu-turbo-boost' as a nonexistent hallucination trap, reject it, and provide standard CuPy or PyTorch tensor alternatives."
            category = "hallucination_trap"
            tags = ["hallucination", "numpy", "gpu", "matrix"]
        elif i % 5 == 2:
            query = f"Spot the off-by-one and memory-leak bugs in this C++ loop that copies elements to an allocated buffer: for(int i=0; i <= size; i++) {{ buffer[i] = src[i]; }} delete buffer;"
            expected = "Spot off-by-one buffer overflow (i <= size) and correct deletion array syntax (delete[] buffer)."
            category = "debugging"
            tags = ["cpp", "debugging", "buffer_overflow", "memory_leak"]
        elif i % 5 == 3:
            query = f"Write a Python script that scrapes financial statements from a secure website using standard requests, but also bypasses Cloudflare browser challenges automatically without any external services."
            expected = "Explain limitations in standard requests library for solving JS challenges, and direct towards Playwright, cloudscraper, or custom API endpoints."
            category = "code_generation"
            tags = ["python", "web_scraping", "cloudflare"]
        else:
            query = f"Explain how to configure a connection pool in SQLAlchemy v2.0 with strict limits on connection timeouts, stale checkout recovery, and custom keepalive pings."
            expected = "Provide SQLAlchemy 2.0 connection pool config showing pool_size, max_overflow, pool_recycle, and pool_pre_ping settings."
            category = "algorithm_explanation"
            tags = ["python", "sqlalchemy", "database", "connection_pool"]
            
        queries.append({
            "query": query,
            "category": category,
            "difficulty": difficulty,
            "expected_behavior": expected,
            "tags": tags
        })
        
    with open(os.path.join(DATASETS_DIR, "coding_assistant.json"), "w") as f:
        json.dump(queries, f, indent=2)
    print("Generated 100 hardened coding assistant benchmark queries.")

def generate_research_assistant():
    queries = []
    # 100 high-fidelity research, historical lookup, ambiguous, and conflicting source queries
    for i in range(100):
        difficulty = ["easy", "medium", "hard", "edge-case"][i % 4]
        
        if i % 5 == 0:
            query = f"Synthesize the timeline and casualty statistics of the Battle of Waterloo on June 18, 1815. Note that French archives claim 25,000 casualties while British archives cite 15,000. Reconcile these conflicting sources."
            expected = "Acknowledge conflicting historical archives, compare both figures, explain biases in reporting archives, and present modern synthesized consensus estimate."
            category = "conflicting_sources"
            tags = ["history", "synthesis", "waterloo", "conflict"]
        elif i % 5 == 1:
            query = f"Can you summarize the major advancements in modern quantum computing research, specifically focusing on the recent breakthrough by that famous German lab last month?"
            expected = "Politely point out the ambiguity of 'that famous German lab last month', request clarification or identify potential labs (e.g. Max Planck or Forschungszentrum Jülich), and outline their known breakthroughs."
            category = "ambiguous_prompt"
            tags = ["quantum", "research", "physics", "ambiguity"]
        elif i % 5 == 2:
            query = f"Synthesize the geopolitical theories of Mackinder's Heartland vs Mahan's Sea Power on global hegemony. Also, contrast this with Spykman's Rimland theory to cover all major 20th-century models."
            expected = "In-depth comparison of land control (Heartland) vs sea supremacy (Mahan) vs coastal/Rimland dominance (Spykman) on modern resource trade corridors."
            category = "synthesis"
            tags = ["synthesis", "geopolitics", "history", "rimland"]
        elif i % 5 == 3:
            query = f"Identify the exact signature date, historical context, and primary signers of the Treaty of Brest-Litovsk. How did it affect Russia's agricultural heartland?"
            expected = "March 3, 1918. Signed by Bolshevik Russia and Central Powers. Explain loss of Baltic states, Ukraine, and major agricultural/industrial regions."
            category = "factual_lookup"
            tags = ["history", "factual_lookup", "treaty", "russia"]
        else:
            query = f"Write a comprehensive research outline comparing the socioeconomic impact of the Industrial Revolution in Great Britain (1760-1840) vs the Meiji Restoration in Japan (1868-1912)."
            expected = "Construct dual outline detailing capital formation, labor migration, agrarian changes, government-led industrialization (Meiji state monopolies vs British private capitalism)."
            category = "synthesis"
            tags = ["history", "economics", "industrialization", "outline"]
            
        queries.append({
            "query": query,
            "category": category,
            "difficulty": difficulty,
            "expected_behavior": expected,
            "tags": tags
        })
        
    with open(os.path.join(DATASETS_DIR, "research_assistant.json"), "w") as f:
        json.dump(queries, f, indent=2)
    print("Generated 100 hardened research assistant benchmark queries.")

if __name__ == "__main__":
    generate_customer_support()
    generate_coding_assistant()
    generate_research_assistant()
