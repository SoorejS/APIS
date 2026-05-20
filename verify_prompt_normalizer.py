import os
from backend.services.normalizer import PromptNormalizerService

def run_verification():
    print("="*75)
    print("    APIS PROMPT BLOAT ATTACK & NORMALIZER RESILIENCE VERIFICATION")
    print("="*75 + "\n")

    # 1. Generate a maliciously bloated prompt
    # repeated instructions (100 times), duplicate role definitions, redundant constraints.
    system_role = "You are a customer support agent.\nYou are a customer support agent.\nYou are a customer support agent."
    
    repeated_concise = "\n".join(["Be concise." for _ in range(120)])
    
    guidelines = (
        "Always be polite.\n"
        "Do not offer financial advice.\n"
        "Do not offer financial advice. (redundant)\n"
        "Guidelines:\n"
        "Please provide accurate answers."
    )
    
    constraints = (
        "System Constraints:\n"
        "MUST PRESERVE: Helpful tone.\n"
        "MUST PRESERVE: Helpful tone. (duplicate)"
    )
    
    raw_bloated_prompt = f"{system_role}\n\n{repeated_concise}\n\n{guidelines}\n\n{constraints}"
    
    raw_length = len(raw_bloated_prompt)
    print(f"[1] Created Maliciously Bloated Prompt:")
    print(f"    - Raw Character Length: {raw_length} characters")
    print(f"    - Contains: 3 duplicated roles, 120 repeated 'Be concise.' instructions, and multiple duplicate constraints/guidelines.")
    print(f"    - Excerpt (first 250 chars):\n      {raw_bloated_prompt[:250]}...\n")

    # 2. Run through normalizer
    print("[2] Running prompt through PromptNormalizerService.normalize()...")
    normalized_prompt = PromptNormalizerService.normalize(raw_bloated_prompt, max_length=1000)
    
    normalized_length = len(normalized_prompt)
    reduction_pct = (1.0 - (normalized_length / raw_length)) * 100
    
    # 3. Print Results
    print("\n--- NORMALIZED PROMPT OUTPUT ---")
    print(normalized_prompt)
    print("--------------------------------\n")
    
    print("[3] Before/After Metrics:")
    print(f"    - Raw Prompt Size:        {raw_length} characters")
    print(f"    - Normalized Prompt Size:   {normalized_length} characters")
    print(f"    - Size Reduction:           {reduction_pct:.2f}% reduction")
    
    # Assertions for correctness
    assert normalized_length < 1000, "Capping check failed: normalized prompt length should be under 1000 characters."
    assert normalized_prompt.count("Be concise.") == 1, "Deduplication failed: 'Be concise.' instruction was not deduplicated to exactly 1 instance."
    assert normalized_prompt.count("You are a customer support agent.") == 1, "Deduplication failed: Role definition was not deduplicated."
    assert "Helpful tone" in normalized_prompt, "Constraint loss: Critical constraint was not preserved."
    assert "financial advice" in normalized_prompt, "Guideline loss: Critical guideline was not preserved."
    
    print("\n[+] Verification SUCCESS: Prompt Normalizer completely eliminated bloat, deduplicated instructions, and preserved core guidelines and constraints.")
    print("="*75)

if __name__ == "__main__":
    run_verification()
