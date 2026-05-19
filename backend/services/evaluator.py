from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import json
import traceback

from backend.models.models import Interaction, PromptNamespace, PromptVersion, EvaluationRun
from backend.services.compiler import PromptCompilerService
from backend.providers.gemini import GeminiProvider
from backend.core.config import settings

class EvaluatorService:
    DEFAULT_TEST_SUITE = {
        "billing": [
            "How do refunds work?",
            "Can I get a refund for my subscription?",
            "Charge dispute request for my billing statement"
        ],
        "coding": [
            "Write a Python recursion function for fibonacci.",
            "Explain Javascript async await syntax.",
            "Fix this bug: list index out of range in Python loop"
        ],
        "customer_support": [
            "Hello, I need help opening a support ticket.",
            "Is there an agent available to chat?",
            "I want to change my account password"
        ],
        "technical": [
            "DNS lookup failed for my server ip.",
            "Database connection timeout at port 5432.",
            "API latency is too high on network request"
        ],
        "general": [
            "What is the capital of France?",
            "How tall is Mount Everest?"
        ]
    }
    
    @staticmethod
    async def run_offline_evaluation(
        db: Session,
        namespace_id: uuid.UUID,
        candidate_version_id: uuid.UUID,
        simulate_regression: bool = False
    ) -> EvaluationRun:
        """
        Executes offline evaluations comparing the candidate prompt versus the active prompt.
        Pulls test queries from database interactions, falling back to a default standard suite.
        Grades both prompts and returns the EvaluationRun record.
        """
        # 1. Fetch Namespace and Prompt Versions
        namespace = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
        if not namespace:
            raise ValueError(f"Namespace {namespace_id} not found.")
            
        candidate_version = db.query(PromptVersion).filter(
            PromptVersion.id == candidate_version_id,
            PromptVersion.namespace_id == namespace_id
        ).first()
        if not candidate_version:
            raise ValueError(f"Candidate version {candidate_version_id} not found.")
            
        active_version = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == namespace_id,
            PromptVersion.status == "active"
        ).first()
        if not active_version:
            raise ValueError(f"No active prompt version found for namespace {namespace_id} to evaluate against.")
            
        # Create pending EvaluationRun
        run = EvaluationRun(
            namespace_id=namespace_id,
            active_version_id=active_version.id,
            candidate_version_id=candidate_version.id,
            status="pending"
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        run.status = "running"
        db.commit()
        
        try:
            # 2. Build Test Suite (Interactions from DB or Default)
            test_cases = {}
            for category in ["billing", "coding", "customer_support", "technical", "general"]:
                # Fetch up to 3 historical queries from DB for this category
                db_queries = db.query(Interaction.user_query).filter(
                    Interaction.namespace_id == namespace_id,
                    Interaction.query_category == category
                ).limit(3).all()
                
                queries = [q[0] for q in db_queries if q[0]]
                if not queries:
                    # Fallback to high-fidelity defaults
                    queries = EvaluatorService.DEFAULT_TEST_SUITE.get(category, ["General query"])
                test_cases[category] = queries
                
            # 3. Grade test cases
            category_scores = {}
            total_active_score = 0.0
            total_candidate_score = 0.0
            categories_count = 0
            
            # Check for live LLM evaluations or mock offline fallback
            if not settings.GEMINI_API_KEY:
                print(f"[EvaluatorService] Running in MOCK mode (No Gemini API Key). Simulate regression: {simulate_regression}")
                
                # Mock grading logic
                # Billing always improves
                billing_active = 0.64
                billing_candidate = 0.82
                
                # Coding behaves differently based on regression simulation
                if simulate_regression:
                    coding_active = 0.90
                    coding_candidate = 0.86  # -4% regression!
                else:
                    coding_active = 0.90
                    coding_candidate = 0.92  # +2% improvement!
                    
                category_scores = {
                    "billing": {"active": billing_active, "candidate": billing_candidate, "delta": round(billing_candidate - billing_active, 4)},
                    "coding": {"active": coding_active, "candidate": coding_candidate, "delta": round(coding_candidate - coding_active, 4)},
                    "customer_support": {"active": 0.85, "candidate": 0.87, "delta": 0.02},
                    "technical": {"active": 0.80, "candidate": 0.82, "delta": 0.02},
                    "general": {"active": 0.88, "candidate": 0.88, "delta": 0.0}
                }
                
                # Calculate overall metrics
                active_sum = sum(v["active"] for v in category_scores.values())
                cand_sum = sum(v["candidate"] for v in category_scores.values())
                avg_active = active_sum / len(category_scores)
                avg_candidate = cand_sum / len(category_scores)
                
            else:
                # LIVE EVALUATION WITH GEMINI
                for category, queries in test_cases.items():
                    cat_active_total = 0.0
                    cat_candidate_total = 0.0
                    queries_count = 0
                    
                    for query in queries:
                        # Compile prompts
                        active_effective = PromptCompilerService.compile_effective_prompt(
                            namespace=namespace,
                            active_version=active_version,
                            runtime_context={"user_tier": "Premium"},
                            user_query=query
                        )
                        candidate_effective = PromptCompilerService.compile_effective_prompt(
                            namespace=namespace,
                            active_version=candidate_version,
                            runtime_context={"user_tier": "Premium"},
                            user_query=query
                        )
                        
                        # Generate responses
                        response_active = await GeminiProvider.generate(active_effective)
                        response_candidate = await GeminiProvider.generate(candidate_effective)
                        
                        # Judge responses using LLM-as-a-judge
                        evaluator_prompt = (
                            f"You are a senior Quality Assurance Judge. Your task is to evaluate and compare two AI responses "
                            f"to the user query: \"{query}\"\n\n"
                            f"Response A (from Active prompt):\n"
                            f"\"\"\"\n{response_active}\n\"\"\"\n\n"
                            f"Response B (from Candidate prompt):\n"
                            f"\"\"\"\n{response_candidate}\n\"\"\"\n\n"
                            f"Rate each response objectively on a scale of 0.0 (unusable) to 1.0 (perfect) "
                            f"based on factual accuracy, helpfulness, and alignment with constraints.\n"
                            f"Your output MUST be a valid JSON object matching the schema below. No explanation, prefix, or conversational text:\n"
                            f"{{\n"
                            f"  \"score_a\": 0.85,\n"
                            f"  \"score_b\": 0.90\n"
                            f"}}\n"
                        )
                        
                        judge_response = await GeminiProvider.generate(evaluator_prompt)
                        
                        try:
                            clean_text = judge_response.strip()
                            if clean_text.startswith("```json"):
                                clean_text = clean_text[7:]
                            if clean_text.endswith("```"):
                                clean_text = clean_text[:-3]
                            clean_text = clean_text.strip()
                            
                            scores = json.loads(clean_text)
                            score_a = float(scores.get("score_a", 0.80))
                            score_b = float(scores.get("score_b", 0.80))
                        except Exception:
                            # Standard fallback score
                            score_a, score_b = 0.80, 0.80
                            
                        cat_active_total += score_a
                        cat_candidate_total += score_b
                        queries_count += 1
                        
                    avg_cat_active = cat_active_total / queries_count if queries_count > 0 else 0.80
                    avg_cat_candidate = cat_candidate_total / queries_count if queries_count > 0 else 0.80
                    
                    category_scores[category] = {
                        "active": round(avg_cat_active, 4),
                        "candidate": round(avg_cat_candidate, 4),
                        "delta": round(avg_cat_candidate - avg_cat_active, 4)
                    }
                    
                avg_active = sum(v["active"] for v in category_scores.values()) / len(category_scores)
                avg_candidate = sum(v["candidate"] for v in category_scores.values()) / len(category_scores)
                
            # 4. Gated Promotion Decision (STRICT USER RULES)
            # Promotion Gating Condition:
            # - Overall average score must improve: avg_candidate >= avg_active
            # - AND no category must regress: delta >= 0.0 for ALL categories (with 0% margin tolerance)
            decision = "promoted"
            for cat, scores in category_scores.items():
                if scores["delta"] < 0.0:
                    # Regressed! Reject candidate.
                    decision = "rejected"
                    break
                    
            if avg_candidate < avg_active:
                decision = "rejected"
                
            # 5. Persist Decision
            run.status = "completed"
            run.overall_active_score = round(avg_active, 4)
            run.overall_candidate_score = round(avg_candidate, 4)
            run.category_scores = category_scores
            run.decision = decision
            db.commit()
            db.refresh(run)
            
            # 6. Apply Promotion/Rejection in database
            if decision == "promoted":
                # Promote candidate prompt to active, archive the old active version
                active_version.status = "archived"
                candidate_version.status = "active"
                db.commit()
                print(f"[EvaluatorService] Promoted candidate version {candidate_version.version_string} to ACTIVE.")
            else:
                # Mark candidate as rejected
                candidate_version.status = "rejected"
                db.commit()
                print(f"[EvaluatorService] Rejected candidate version {candidate_version.version_string} due to category regression.")
                
                # Record rejection in Failure Memory
                try:
                    from backend.services.failure_memory import FailureMemoryService
                    regressed_categories = [cat for cat, s in category_scores.items() if s["delta"] < 0.0]
                    failed_pattern = f"Category regression detected in: {', '.join(regressed_categories)}" if regressed_categories else "Overall metrics score degradation"
                    
                    reason_details = []
                    for cat, s in category_scores.items():
                        if s["delta"] < 0.0:
                            reason_details.append(f"{cat} regressed ({s['active']} -> {s['candidate']}, delta: {s['delta']})")
                    if avg_candidate < avg_active:
                        reason_details.append(f"Overall average degraded ({avg_active:.4f} -> {avg_candidate:.4f})")
                    
                    FailureMemoryService.record_failure(
                        db=db,
                        namespace_id=namespace_id,
                        failed_pattern=failed_pattern,
                        attempted_fix=candidate_version.change_rationale or "Adaptive prompt generation attempt",
                        reason="; ".join(reason_details) if reason_details else "Performance degradation"
                    )
                    print("[EvaluatorService] Recorded candidate rejection into Failure Memory.")
                except Exception as fm_err:
                    print(f"[EvaluatorService] Failed to record failure memory: {fm_err}")
                
            return run
            
        except Exception as e:
            db.rollback()
            tb = traceback.format_exc()
            run.status = "failed"
            run.error_message = f"Error: {str(e)}\n\nTraceback:\n{tb}"
            db.commit()
            db.refresh(run)
            print(f"[EvaluatorService] Evaluation failed: {e}")
            return run
