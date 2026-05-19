import json
from sqlalchemy.orm import Session
from backend.providers.gemini import GeminiProvider
from backend.core.config import settings
from backend.models.models import PromptNamespace, PromptVersion, QualityPattern, Interaction

class IterationEngine:
    @staticmethod
    async def generate_candidate(
        db: Session,
        namespace_id,
        current_version: PromptVersion,
        active_patterns: list
    ) -> tuple:
        """
        Generates v1.1-candidate system prompt using Gemini.
        Returns: (candidate_prompt, change_rationale)
        """
        # 1. Fetch Namespace constraints
        namespace = db.query(PromptNamespace).filter(PromptNamespace.id == namespace_id).first()
        constraints = namespace.constraints or {}
        must_preserve = constraints.get("must_preserve", [])
        cannot_modify = constraints.get("cannot_modify", [])
        
        # 2. Format observed problems from patterns
        problems = []
        for p in active_patterns:
            problems.append(
                f"- Category '{p.query_category}' received high {p.signal_type} feedback "
                f"(negative rate: {p.negative_rate:.2f}, count: {p.signal_count})"
            )
        problems_str = "\n".join(problems) if problems else "- General negative feedback signals detected."
        
        # 3. Format constraints string
        constraints_str = (
            f"MUST PRESERVE:\n" + "\n".join([f"- {c}" for c in must_preserve]) + "\n\n"
            f"CANNOT MODIFY/DO:\n" + "\n".join([f"- {c}" for c in cannot_modify])
        )
        
        # 3b. Fetch Failure Memory to prevent repeating historical mistakes
        from backend.services.failure_memory import FailureMemoryService
        failures_str = FailureMemoryService.get_formatted_failures_prompt(db, namespace_id)
        
        # 4. Mock / Offline fallback check
        if not settings.GEMINI_API_KEY:
            # High-fidelity candidate generator mock (cohesive rewrite simulation)
            print("[IterationEngine] Running in MOCK mode (No Gemini API Key)")
            
            # Simulated high-quality prompt rewrite directly resolving the billing feedback
            candidate_prompt = (
                "You are a professional customer support agent. Resolve customer queries with empathy.\n"
                "## OPERATIONAL GUIDELINES:\n"
                "- Provide clear, direct assistance.\n"
                "- Keep answers highly concise and verify factual details under billing queries.\n"
                "## SYSTEM CONSTRAINTS:\n"
                "- Protect branding guidelines.\n"
                "- Refund policy limit: max 30 days"
            )
            
            rationale = (
                "Aggregated feedback signal engine identified high thumbs_down rate (62%) on billing queries. "
                "Rewrote prompt to integrate conciseness instructions and enforce rigorous verification of billing information."
            )
            return candidate_prompt, rationale

        # 5. Build prompt for Gemini
        system_instruction = (
            "You are a Senior Principal AI Prompt Engineer. Your task is to optimize an existing system prompt "
            "to address observed negative user feedback, while strictly preserving core legal, policy, and branding constraints.\n\n"
            "STRICT RULES:\n"
            "1. You MUST preserve all constraints in the list perfectly. Do not remove, alter, or dilute them.\n"
            "2. Never mutate or alter any runtime context template placeholders (e.g. {{user_tier}} or {{query}} if any exist).\n"
            "3. Focus changes selectively (maximum delta 30%). Do not rewrite the prompt from scratch. Adjust wording to guide the LLM better.\n"
            "4. Do not perform empty/no-op rewrites. If the original prompt is already optimal, leave it as is.\n"
            "5. Do NOT simply append 'optimization notes', 'guidelines' or 'addendums' at the end of the prompt. "
            "Instead, refactor and seamlessly integrate the optimization directly into the main instructions, keeping a clean, unified structure.\n"
            "6. You must output your response as a valid JSON object matching the requested schema. No conversational prefix or markdown styling outside of JSON."
        )
        
        user_prompt = (
            f"Original System Prompt Content:\n"
            f"\"\"\"\n{current_version.content}\n\"\"\"\n\n"
            f"Observed Quality Problems & User Feedback:\n"
            f"\"\"\"\n{problems_str}\n\"\"\"\n\n"
            f"Hard Constraints to Protect:\n"
            f"\"\"\"\n{constraints_str}\n\"\"\"\n\n"
            f"{failures_str}\n"
            f"Please output a JSON object containing:\n"
            f"{{\n"
            f"  \"candidate_prompt\": \"The fully optimized system prompt text.\",\n"
            f"  \"rationale\": \"Structured explanation of what modifications were performed to address the feedback.\"\n"
            f"}}\n"
        )
        
        # Call Gemini Provider via aggregate prompt
        combined_prompt = f"{system_instruction}\n\n{user_prompt}"
        response_text = await GeminiProvider.generate(combined_prompt)
        
        # Parse JSON output from Gemini
        try:
            # Strip markdown code blocks if any
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            candidate_prompt = data.get("candidate_prompt", current_version.content)
            rationale = data.get("rationale", "Optimized base prompt based on quality patterns.")
            return candidate_prompt, rationale
        except Exception as e:
            print(f"[IterationEngine] Failed to parse Gemini structured JSON: {e}. Raw response: {response_text}")
            # Graceful fallback: return original prompt with slight append
            return current_version.content + "\n\n# Fallback optimization due to parsing failure", "Fallback iteration."
