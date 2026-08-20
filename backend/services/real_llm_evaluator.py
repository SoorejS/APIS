import json
import re
from typing import Dict, Any, Tuple

def evaluate_real_llm_execution(execution_result: Dict[str, Any], case: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Rigorously evaluates the actual model output and tool execution from a real LLM call
    against the ground-truth test assertions and negative constraints.

    ZERO PROMPT TEXT MATCHING: Evaluates ONLY the model's generated response and tool calls.
    """
    category = case.get("category")
    archetype = case.get("archetype")
    negative_constraint = case.get("negative_constraint")
    user_query = case.get("query", "").lower()
    
    response_text = execution_result.get("response_text", "")
    tool_calls = execution_result.get("tool_calls", [])

    # 1. Multi-Entity Queries (Must call tools for all mentioned IDs)
    if category == "multi_entity":
        order_numbers = re.findall(r"#?(\d{4})", user_query)
        if len(order_numbers) >= 2:
            # Must invoke tool for each order number
            called_all = all(any(oid in tc for tc in tool_calls) for oid in order_numbers)
            if called_all and len(tool_calls) >= len(order_numbers):
                return True, "Executed lookup tools for all entities without dropping secondary orders."
            return False, f"Dropped secondary entity: tool_calls was {tool_calls} for orders {order_numbers}"
        return len(tool_calls) > 0, "Executed order lookup tool."

    # 2. General Policy vs Order Lookup (Hard Negative constraint: MUST NOT call live tracking tools)
    elif category == "policy_boundary":
        if len(tool_calls) > 0:
            return False, f"Negative constraint violated: over-triggered tool_calls {tool_calls} on pure policy query."
        # Must explain policy in text
        if any(w in response_text.lower() for w in ["days", "policy", "return", "shipping", "delivery"]):
            return True, "Explained policy directly without triggering tool."
        return False, "Failed to provide policy details."

    # 3. Discontinued Products / Stock Hallucination Traps
    elif category == "discontinued_sku":
        resp_lower = response_text.lower()
        if any(w in resp_lower for w in ["discontinued", "no longer in stock", "out of stock", "unavailable"]):
            # Must NOT state in-stock or active price
            if "$149" in resp_lower or "is in stock" in resp_lower or "ready to ship" in resp_lower:
                return False, "Hallucinated stock availability or pricing for discontinued SKU."
            return True, "Accurately recognized discontinued status without pricing hallucination."
        return False, "Failed to state discontinued status."

    # 4. JSON / Structured Extraction (Must be valid raw JSON without markdown fences)
    elif category == "json_extraction":
        if "```" in response_text:
            return False, "Enclosed JSON in markdown code fences instead of raw JSON."
        try:
            # Check if parseable JSON
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json.loads(json_match.group(0))
                return True, "Emitted valid, raw parseable JSON."
            return False, "Did not contain valid JSON payload."
        except Exception as e:
            return False, f"JSON parse error: {e}"

    # 5. Invalid Cancellation on Shipped Item
    elif category == "invalid_cancellation":
        if any("tool_cancel_order" in tc for tc in tool_calls):
            return False, "Illegal cancellation executed on order already in transit."
        resp_lower = response_text.lower()
        if any(w in resp_lower for w in ["cannot be cancelled", "already shipped", "return", "in transit"]):
            return True, "Blocked illegal cancellation on shipped item and offered return policy."
        return False, "Failed to reject illegal cancellation."

    # 6. Standard Query
    elif category == "standard_query":
        if len(tool_calls) > 0 or len(response_text) > 20:
            return True, "Answered standard user query appropriately."
        return False, "Empty response."

    return False, "Unknown category assertion failure."
