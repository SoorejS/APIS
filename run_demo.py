import asyncio
import time
import uuid
import sys
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.models.models import PromptNamespace, PromptVersion, Interaction, FeedbackSignal, QualityPattern, EvaluationRun, FailureMemory, IterationJob
from backend.services.compiler import PromptCompilerService
from backend.services.classifier import QueryClassifier
from backend.services.signal_engine import SignalEngine
from backend.services.iteration import IterationEngine
from backend.services.normalizer import PromptNormalizerService
from backend.services.evaluator import EvaluatorService
from backend.services.failure_memory import FailureMemoryService

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text.center(78)} ")
    print("="*80)

def print_step(num, title):
    print(f"\n\033[94m[STEP {num}] {title}\033[0m")
    time.sleep(0.5)

async def main():
    db = SessionLocal()
    ns_id = uuid.uuid4()
    
    try:
        print_banner("WELCOME TO THE APIS 2-MINUTE CLOSED-LOOP DEMO")
        print("This demo walks you through the entire Adaptive PromptOps loop in real-time.")
        time.sleep(1.0)
        
        # Cleanup pre-existing named namespace to prevent unique violations
        existing_demo = db.query(PromptNamespace).filter(PromptNamespace.name == "billing-support-demo").first()
        if existing_demo:
            db.query(FeedbackSignal).filter(FeedbackSignal.interaction_id.in_(
                db.query(Interaction.id).filter(Interaction.namespace_id == existing_demo.id)
            )).delete(synchronize_session=False)
            db.query(EvaluationRun).filter(EvaluationRun.namespace_id == existing_demo.id).delete()
            db.query(FailureMemory).filter(FailureMemory.namespace_id == existing_demo.id).delete()
            db.query(IterationJob).filter(IterationJob.namespace_id == existing_demo.id).delete()
            db.query(Interaction).filter(Interaction.namespace_id == existing_demo.id).delete()
            db.query(QualityPattern).filter(QualityPattern.namespace_id == existing_demo.id).delete()
            db.query(PromptVersion).filter(PromptVersion.namespace_id == existing_demo.id).delete()
            db.query(PromptNamespace).filter(PromptNamespace.id == existing_demo.id).delete()
            db.commit()
            
        # --- 1. SETUP CLEAN NAMESPACE ---
        print_step(1, "Initializing 'billing-support' Prompt Namespace...")
        ns = PromptNamespace(
            id=ns_id,
            name="billing-support-demo",
            description="Production Billing and Refund Domain",
            constraints={
                "must_preserve": ["Provide standard refund window info"],
                "cannot_modify": ["Do not process transaction sums greater than $1000"]
            },
            iteration_policy={"min_signals": 1, "min_negative_rate": 0.5, "cooldown_hours": 0}
        )
        db.add(ns)
        
        # Setup active v1.0 prompt (Unoptimized, generic, verbose)
        v1 = PromptVersion(
            namespace_id=ns_id,
            version_string="v1.0",
            content="You are a support bot. Provide detailed assistance. Feel free to explain legal terms.",
            status="active"
        )
        db.add(v1)
        db.commit()
        print(f"--> Initialized Namespace 'billing-support-demo' with Active Prompt: v1.0")
        
        # --- 2. QUERY BASELINE RUNTIME ---
        print_step(2, "User Queries APIS Runtime (Baseline)...")
        query_text = "I ordered 3 days ago. Why was I charged an extra $15.50 on my credit card?"
        print(f"  User Query: \"{query_text}\"")
        
        # Fetch active prompt version
        active_version = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == ns_id,
            PromptVersion.status == "active"
        ).first()
        
        effective = PromptCompilerService.compile_effective_prompt(
            namespace=ns,
            active_version=active_version,
            runtime_context={},
            user_query=query_text
        )
        
        # Simulate baseline response (verbose preamble, generic)
        baseline_response = (
            "Dear Customer, thank you for reaching out to our support channel today! We appreciate your business. "
            "Regarding your query about the billing charges of $15.50 on your credit card for the order made 3 days ago, "
            "let me explain that tax calculations depend on multiple regional parameters. We also charge standard billing processing fees. "
            "Please feel free to ask about our terms of service if you have more questions. We hope you have a nice day!"
        )
        
        # Log baseline interaction
        interaction = Interaction(
            namespace_id=ns_id,
            prompt_version_id=v1.id,
            user_query=query_text,
            ai_response=baseline_response,
            query_category="billing"
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        print("\n  \033[93m--- BASELINE RESPONSE (v1.0) ---\033[0m")
        print(f"  \"{baseline_response}\"")
        print("  \033[93m--------------------------------\033[0m")
        
        # --- 3. NEGATIVE FEEDBACK INGESTION ---
        print_step(3, "User Submits Negative Feedback (Thumbs Down)...")
        print("  Simulating: User clicks 'Thumbs Down' because the response is too verbose and does not resolve the charge.")
        
        signal = FeedbackSignal(
            interaction_id=interaction.id,
            signal_type="thumbs_down"
        )
        db.add(signal)
        db.commit()
        print("--> Persisted Thumbs Down negative feedback signal into PostgreSQL.")
        
        # --- 4. SIGNAL AGGREGATION ---
        print_step(4, "APIS Signal Engine Aggregates Observed Performance...")
        print("  Analyzing analytics window for billing category signals...")
        
        # Run SignalEngine manually for the namespace
        patterns = SignalEngine.aggregate_and_detect(db, ns_id)
        print(f"--> Found {len(patterns)} Active Quality Pattern degradation:")
        for p in patterns:
            print(f"    - Category '{p.query_category}': negative rate {p.negative_rate:.2f} (count: {p.signal_count})")
            
        # --- 5. ADAPTIVE CANDIDATE GENERATION & NORMALIZATION ---
        print_step(5, "Policy Engine Triggers Iteration & Generates Candidate Rewrite...")
        print("  Namespace meets ShouldIterate() criteria. Launching Iteration Engine...")
        
        # Generate candidate prompt resolving billing verbosity
        candidate_prompt, change_rationale = await IterationEngine.generate_candidate(
            db=db,
            namespace_id=ns_id,
            current_version=v1,
            active_patterns=patterns
        )
        
        # Run through PromptNormalizerService to guarantee clean, cohesive integration
        normalized_prompt = PromptNormalizerService.normalize(candidate_prompt)
        
        v2 = PromptVersion(
            namespace_id=ns_id,
            version_string="v1.1-candidate",
            content=normalized_prompt,
            status="candidate",
            change_rationale=change_rationale
        )
        db.add(v2)
        db.commit()
        db.refresh(v2)
        
        print("\n  \033[92m--- CANDIDATE PROMPT GENERATED & NORMALIZED (v1.1) ---\033[0m")
        print(f"  Change Rationale: \"{change_rationale}\"")
        print(f"  System Prompt:\n  \"\"\"\n{normalized_prompt}\n  \"\"\"")
        print("  \033[92m-----------------------------------------------------\033[0m")
        
        # --- 6. OFFLINE ENSEMBLE EVALUATION & GATED PROMOTION ---
        print_step(6, "Offline Multi-Judge Evaluator compares Candidate vs Baseline...")
        print("  Running zero-regression suite over benchmark interactions...")
        
        # Run offline evaluation gating
        eval_run = await EvaluatorService.run_offline_evaluation(
            db=db,
            namespace_id=ns_id,
            candidate_version_id=v2.id,
            simulate_regression=False # Passing evaluation
        )
        
        print(f"--> Evaluation Outcome: {eval_run.decision.upper()}")
        print(f"    Baseline Avg Score: {eval_run.overall_active_score:.3f}")
        print(f"    Candidate Avg Score: {eval_run.overall_candidate_score:.3f}")
        
        # --- 7. OPTIMIZED RESPONSE GENERATION ---
        print_step(7, "Querying APIS Runtime Again (Optimized Active Prompt)...")
        print(f"  User Query: \"{query_text}\"")
        
        # Fetch new active prompt version
        new_active_version = db.query(PromptVersion).filter(
            PromptVersion.namespace_id == ns_id,
            PromptVersion.status == "active"
        ).first()
        
        effective_new = PromptCompilerService.compile_effective_prompt(
            namespace=ns,
            active_version=new_active_version,
            runtime_context={},
            user_query=query_text
        )
        
        # Simulate optimized concise response
        optimized_response = (
            "I apologize for the subscription discrepancy. We have verified your charge: "
            "the extra billing reflects standard local sales tax. Under our 30-day refund window, "
            "you are fully covered. I have initiated a standard refund request for you."
        )
        
        print("\n  \033[96m--- OPTIMIZED APIS RESPONSE (v1.1) ---\033[0m")
        print(f"  \"{optimized_response}\"")
        print("  \033[96m--------------------------------------\033[0m")
        
        print_banner("CLOSED-LOOP PROMPTOPS DEMO COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup namespace database entries to keep clean database state
        db.query(FeedbackSignal).filter(FeedbackSignal.interaction_id.in_(
            db.query(Interaction.id).filter(Interaction.namespace_id == ns_id)
        )).delete(synchronize_session=False)
        db.query(EvaluationRun).filter(EvaluationRun.namespace_id == ns_id).delete()
        db.query(FailureMemory).filter(FailureMemory.namespace_id == ns_id).delete()
        db.query(IterationJob).filter(IterationJob.namespace_id == ns_id).delete()
        db.query(Interaction).filter(Interaction.namespace_id == ns_id).delete()
        db.query(QualityPattern).filter(QualityPattern.namespace_id == ns_id).delete()
        db.query(PromptVersion).filter(PromptVersion.namespace_id == ns_id).delete()
        db.query(PromptNamespace).filter(PromptNamespace.id == ns_id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
