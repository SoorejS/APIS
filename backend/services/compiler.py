from backend.models.models import PromptNamespace, PromptVersion
from typing import Dict, Any

class PromptCompilerService:
    @staticmethod
    def compile_effective_prompt(
        namespace: PromptNamespace,
        active_version: PromptVersion,
        runtime_context: Dict[str, Any],
        user_query: str
    ) -> str:
        """
        Effective Prompt = 
          [BASE PROMPT] + 
          [CONSTRAINT LAYER] + 
          [RUNTIME CONTEXT]
        """
        
        # 1. Base Prompt
        compiled = f"SYSTEM INSTRUCTIONS:\n{active_version.content}\n\n"
        
        # 2. Constraint Layer
        if namespace.constraints:
            compiled += "STRICT CONSTRAINTS:\n"
            must_preserve = namespace.constraints.get("must_preserve", [])
            for constraint in must_preserve:
                compiled += f"- MUST PRESERVE: {constraint}\n"
                
            cannot_modify = namespace.constraints.get("cannot_modify", [])
            for constraint in cannot_modify:
                compiled += f"- CANNOT MODIFY/DO: {constraint}\n"
            compiled += "\n"
            
        # 3. Runtime Context (Variables)
        if runtime_context:
            compiled += "RUNTIME CONTEXT:\n"
            for k, v in runtime_context.items():
                compiled += f"{k}: {v}\n"
            compiled += "\n"
            
        # 4. User Query
        compiled += f"USER QUERY:\n{user_query}\n"
        
        return compiled
