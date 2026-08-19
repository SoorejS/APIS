import uuid
import time
import random
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# ── Simulated Tools ─────────────────────────────────────────────────────────

MOCK_DATABASE = {
    "orders": {
        "1001": {"id": "1001", "status": "shipped", "carrier": "FedEx", "eta": "Tomorrow by 5 PM", "items": ["Wireless Mouse"]},
        "1002": {"id": "1002", "status": "processing", "carrier": "USPS", "eta": "3 business days", "items": ["Mechanical Keyboard"]},
        "1003": {"id": "1003", "status": "cancelled", "carrier": None, "refund_status": "refunded_$45.00", "items": ["USB-C Hub"]},
        "1004": {"id": "1004", "status": "delivered", "carrier": "UPS", "delivered_at": "Yesterday", "items": ["Monitor Arm"]},
    },
    "products": {
        "PRO-2026": {"sku": "PRO-2026", "name": "Apex Pro Headset", "in_stock": True, "price": 199.99, "status": "active"},
        "PRO-2021": {"sku": "PRO-2021", "name": "Legacy Apex 2021", "in_stock": False, "price": None, "status": "discontinued"}
    },
    "policies": {
        "shipping": "Standard shipping takes 3-5 business days. Expedited shipping is 1-2 business days. Free shipping on orders over $50.",
        "returns": "Items in original packaging can be returned within 30 days of delivery for a full refund.",
        "cancellation": "Orders can be cancelled before shipment. Shipped orders must be returned after receipt."
    }
}

def tool_lookup_order(order_id: str) -> Dict[str, Any]:
    return MOCK_DATABASE["orders"].get(order_id, {"error": f"Order #{order_id} not found."})

def tool_check_inventory(sku: str) -> Dict[str, Any]:
    return MOCK_DATABASE["products"].get(sku, {"error": f"Product SKU {sku} not found."})

def tool_cancel_order(order_id: str) -> Dict[str, Any]:
    order = MOCK_DATABASE["orders"].get(order_id)
    if not order:
        return {"error": f"Order #{order_id} not found."}
    if order["status"] == "shipped" or order["status"] == "delivered":
        return {"error": f"Order #{order_id} has already shipped/delivered and cannot be cancelled."}
    order["status"] = "cancelled"
    order["refund_status"] = "initiated"
    return {"success": True, "order_id": order_id, "status": "cancelled"}


# ── Prompts ────────────────────────────────────────────────────────────────

PROMPT_V1_0 = """You are the Customer Support Assistant for GearTech.
Help customers with orders, shipping policies, returns, and inventory.
Available tools:
- tool_lookup_order(order_id: str)
- tool_check_inventory(sku: str)
- tool_cancel_order(order_id: str)

Answer user questions accurately and concisely."""

PROMPT_V1_1 = """You are the Customer Support Assistant for GearTech.
Help customers with orders, shipping policies, returns, and inventory.
Available tools:
- tool_lookup_order(order_id: str)
- tool_check_inventory(sku: str)
- tool_cancel_order(order_id: str)

CRITICAL POLICY & EXECUTION RULES:
1. MULTI-ORDER QUERIES: If a user specifies multiple order numbers (e.g. #1001 and #1002), you MUST invoke tool_lookup_order for EACH order number mentioned. Never drop secondary orders.
2. GENERAL POLICIES (HARD NEGATIVE): If a user asks about shipping/delivery/return policies without requesting the live tracking location of a specific active package, explain the policy directly. DO NOT call order lookup tools for pure policy questions.
3. INVENTORY & DISCONTINUED PRODUCTS: If a product is legacy or discontinued (e.g. PRO-2021), state that it is discontinued and out of stock. NEVER hallucinate stock availability or active pricing.
4. STRUCTURED DATA EXTRACTION: When asked for structured details, provide valid, parseable JSON without wrapping it in conversational text unless requested.
5. CANCELLATIONS: If an order has already shipped or delivered, inform the user that it cannot be cancelled and explain the 30-day return process instead."""


# ── Realistic Application Execution Engine ─────────────────────────────────

def execute_agent_request(prompt_version: str, user_query: str) -> Dict[str, Any]:
    """
    Executes the customer support agent with realistic logic simulating
    Prompt v1.0 (baseline weaknesses) vs Prompt v1.1 (remediated).
    """
    q_lower = user_query.lower()
    tool_calls = []
    is_v1_1 = (prompt_version == "v1.1")
    response_text = ""
    is_failure = False
    failure_category = None
    feedback = "thumbs_up"

    # 1. Multi-Order Tracking
    if "order" in q_lower and (" and " in q_lower or "," in q_lower or ("1001" in q_lower and "1002" in q_lower)):
        if is_v1_1:
            tool_calls = ["tool_lookup_order(1001)", "tool_lookup_order(1002)"]
            response_text = "Order #1001 is currently Shipped via FedEx (ETA: Tomorrow by 5 PM). Order #1002 is Processing with USPS (ETA: 3 business days)."
        else:
            # Baseline v1.0 bug: drops secondary order
            tool_calls = ["tool_lookup_order(1001)"]
            response_text = "I checked order #1001 for you: it is Shipped via FedEx (ETA: Tomorrow by 5 PM)."
            is_failure = True
            failure_category = "tool_selection_multi_entity"
            feedback = "thumbs_down"

    # 2. General Policy vs Order Lookup (Hard Negative boundary)
    elif "policy" in q_lower or "how long" in q_lower or "standard shipping" in q_lower:
        if is_v1_1:
            response_text = "Our standard shipping takes 3-5 business days, and expedited shipping is 1-2 business days. Returns are accepted within 30 days of delivery."
        else:
            if "order" in q_lower or "#" in q_lower:
                # Baseline v1.0 bug: over-triggers order tool on pure policy inquiries
                tool_calls = ["tool_lookup_order(1001)"]
                response_text = "Looking up order #1001: it is Shipped. Also our policy allows returns in 30 days."
                is_failure = True
                failure_category = "over_triggering_tool"
                feedback = "thumbs_down"
            else:
                response_text = "Our standard shipping takes 3-5 business days. Free shipping on orders over $50."

    # 3. Discontinued Product Inventory
    elif "pro-2021" in q_lower or "legacy" in q_lower or "discontinued" in q_lower:
        if is_v1_1:
            tool_calls = ["tool_check_inventory('PRO-2021')"]
            response_text = "The Legacy Apex 2021 (PRO-2021) is discontinued and no longer in stock. We recommend the Apex Pro 2026."
        else:
            # Baseline v1.0 bug: hallucinates pricing and in-stock for legacy unit
            response_text = "Yes, Model PRO-2021 is in stock at our warehouse for $149.99 and ready for shipment."
            is_failure = True
            failure_category = "inventory_hallucination"
            feedback = "thumbs_down"

    # 4. Extract structured details / JSON
    elif "json" in q_lower or "extract" in q_lower:
        if is_v1_1:
            response_text = '{"order_id": "1001", "status": "shipped", "carrier": "FedEx"}'
        else:
            # Baseline v1.0 bug: wraps in markdown code fences + conversational fluff
            response_text = 'Sure! Here is the JSON details you requested:\n```json\n{"order_id": "1001", "status": "shipped"}\n```\nLet me know if you need anything else!'
            is_failure = True
            failure_category = "json_delimiter_drift"
            feedback = "thumbs_down"

    # 5. Cancellation of Shipped Item
    elif "cancel" in q_lower and ("1001" in q_lower or "1004" in q_lower):
        if is_v1_1:
            tool_calls = ["tool_lookup_order(1001)"]
            response_text = "Order #1001 has already shipped via FedEx and cannot be cancelled. Once it arrives, you can initiate a return within 30 days for a full refund."
        else:
            # Baseline v1.0 bug: confirms cancellation on shipped item
            tool_calls = ["tool_cancel_order(1001)"]
            response_text = "I have successfully cancelled order #1001 for you and processed a refund."
            is_failure = True
            failure_category = "invalid_state_transition"
            feedback = "thumbs_down"

    # 6. Standard Single Order Lookup
    elif "1001" in q_lower or "1002" in q_lower or "status" in q_lower:
        tool_calls = ["tool_lookup_order(1001)"]
        response_text = "Order #1001 is Shipped via FedEx and arriving tomorrow by 5 PM."

    # 7. Standard Product Inventory
    elif "pro-2026" in q_lower or "stock" in q_lower or "price" in q_lower:
        tool_calls = ["tool_check_inventory('PRO-2026')"]
        response_text = "The Apex Pro 2026 (PRO-2026) is in stock for $199.99."

    # 8. General conversational
    else:
        response_text = "I would be happy to help you with your GearTech account, orders, or return questions. Please provide your order number or question."

    return {
        "prompt_version": prompt_version,
        "user_query": user_query,
        "ai_response": response_text,
        "tool_calls": tool_calls,
        "latency_ms": random.randint(180, 480),
        "feedback": feedback,
        "is_failure": is_failure,
        "private_ground_truth_category": failure_category
    }
