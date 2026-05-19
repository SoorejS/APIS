import re

class PromptNormalizerService:
    @staticmethod
    def normalize(prompt: str, max_length: int = 1500) -> str:
        """
        Takes a raw system prompt and normalizes it:
        1. Parse structure into canonical sections (System Instructions, Guidelines, Constraints).
        2. Deduplicate instructions by removing redundant or highly overlapping sentences.
        3. Enforce dynamic maximum length budget.
        """
        if not prompt:
            return ""
            
        # 1. Clean whitespace and group lines into clean instructions
        lines = [line.strip() for line in prompt.splitlines()]
        
        sections = {
            "system_role": [],
            "guidelines": [],
            "constraints": []
        }
        
        current_section = "system_role"
        
        # 2. Simple deterministic structural parser
        for line in lines:
            if not line:
                continue
                
            lower_line = line.lower()
            
            # Skip existing markdown headers for sections and just update state
            if lower_line.startswith("#") and ("guideline" in lower_line or "constraint" in lower_line or "role" in lower_line or "instruction" in lower_line):
                if "constraint" in lower_line:
                    current_section = "constraints"
                elif "guideline" in lower_line or "instruction" in lower_line:
                    current_section = "guidelines"
                continue
                
            if "constraint" in lower_line or "must preserve" in lower_line or "cannot modify" in lower_line:
                current_section = "constraints"
                sections[current_section].append(line)
            elif "guideline" in lower_line or "instruction" in lower_line or "note:" in lower_line or "rules:" in lower_line:
                current_section = "guidelines"
                sections[current_section].append(line)
            else:
                sections[current_section].append(line)
                
        # 3. Deduplicate instructions (sentence-level overlap reduction)
        seen_sentences = set()
        deduplicated_role = []
        deduplicated_guidelines = []
        deduplicated_constraints = []
        
        def clean_text_for_comparison(text: str) -> str:
            # Lowercase and strip punctuation/spaces for semantic uniqueness check
            t = text.lower()
            t = re.sub(r'[^a-z0-9]', '', t)
            return t

        # Process system role
        for instr in sections["system_role"]:
            key = clean_text_for_comparison(instr)
            if key not in seen_sentences:
                seen_sentences.add(key)
                deduplicated_role.append(instr)
                
        # Process guidelines
        for instr in sections["guidelines"]:
            key = clean_text_for_comparison(instr)
            if key not in seen_sentences:
                seen_sentences.add(key)
                deduplicated_guidelines.append(instr)
                
        # Process constraints
        for instr in sections["constraints"]:
            key = clean_text_for_comparison(instr)
            if key not in seen_sentences:
                seen_sentences.add(key)
                deduplicated_constraints.append(instr)
                
        # 4. Reconstruct clean, cohesive prompt layout (NO appended mess)
        normalized_parts = []
        if deduplicated_role:
            normalized_parts.append("\n".join(deduplicated_role))
        if deduplicated_guidelines:
            normalized_parts.append("## OPERATIONAL GUIDELINES:\n" + "\n".join(deduplicated_guidelines))
        if deduplicated_constraints:
            normalized_parts.append("## SYSTEM CONSTRAINTS:\n" + "\n".join(deduplicated_constraints))
            
        normalized_prompt = "\n\n".join(normalized_parts)
        
        # 5. Enforce Max Length Budget gracefully
        if len(normalized_prompt) > max_length:
            print(f"[Normalizer] Prompt length ({len(normalized_prompt)}) exceeds budget limit ({max_length}). Enforcing soft truncation.")
            # Gracefully truncate to last full sentence within max_length budget
            truncated = normalized_prompt[:max_length]
            last_period = truncated.rfind(".")
            if last_period != -1:
                normalized_prompt = truncated[:last_period + 1]
            else:
                normalized_prompt = truncated
                
        return normalized_prompt.strip()
