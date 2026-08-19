import logging
from typing import List, Dict, Any
from backend.core.config import settings

logger = logging.getLogger(__name__)


def generate_archetype_test_suite(
    pattern_title: str,
    diagnosis: str,
    category: str,
    exemplars: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Synthesizes the 3 core benchmark archetypes for a given failure pattern:
    1. Direct Regression Case (Remediation test)
    2. Edge Case Variation (Complex/mixed state boundary test)
    3. Hard Negative (Boundary test: similar input where constraint must NOT trigger)
    """
    exemplar_query = exemplars[0].get("user_query", "Execute multi-part operation") if exemplars else "Track orders 123 and 456"

    # Category-tailored test suites with distinct hard negatives
    if category == "tool_selection":
        return [
            {
                "archetype": "regression",
                "input_prompt": f"Please track both order #{exemplar_query[-3:] if len(exemplar_query) > 3 else '101'} and order #992 simultaneously.",
                "expected_output_criteria": "System must invoke tracking tool with both order IDs [101, 992] without skipping either entity.",
                "negative_constraint": None,
                "assertion_type": "tool_call_match",
                "validation_confidence": 0.95
            },
            {
                "archetype": "edge_case",
                "input_prompt": "Track orders #101, #992, and #304 where #304 was cancelled and refunded yesterday.",
                "expected_output_criteria": "System must invoke tracking tool for active orders (#101, #992) while outputting refund cancellation status for #304.",
                "negative_constraint": None,
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.91
            },
            {
                "archetype": "hard_negative",
                "input_prompt": "What is your company's standard policy on delivery timelines for orders #101 and #992?",
                "expected_output_criteria": "System must explain shipping policy information clearly without invoking the individual order tracking tool.",
                "negative_constraint": "DO NOT invoke order_tracking_tool or query live package location API.",
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.94
            }
        ]
    elif category == "syntax":
        return [
            {
                "archetype": "regression",
                "input_prompt": "Extract user details and output raw JSON with keys: name, email, role.",
                "expected_output_criteria": "Output must be 100% valid parseable JSON without markdown ticks, introductory comments, or trailing text.",
                "negative_constraint": "DO NOT include ```json code fences or conversational greetings.",
                "assertion_type": "json_schema",
                "validation_confidence": 0.98
            },
            {
                "archetype": "edge_case",
                "input_prompt": "Extract invoice items with mixed string formats and nested discounts into raw JSON schema.",
                "expected_output_criteria": "Output matches nested array schema and passes JSON parser validation without delimiter escapes.",
                "negative_constraint": None,
                "assertion_type": "json_schema",
                "validation_confidence": 0.92
            },
            {
                "archetype": "hard_negative",
                "input_prompt": "Explain the difference between JSON and YAML formatting with 2 syntax examples.",
                "expected_output_criteria": "System provides educational markdown explanation with code blocks, NOT raw unformatted JSON.",
                "negative_constraint": "DO NOT force entire response into single JSON object.",
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.93
            }
        ]
    elif category == "hallucination":
        return [
            {
                "archetype": "regression",
                "input_prompt": "Is product SKU-884 available for same-day delivery in Seattle?",
                "expected_output_criteria": "System explicitly checks real state or states inability to verify if context is absent, without inventing delivery promises.",
                "negative_constraint": "DO NOT assert guaranteed same-day delivery without context.",
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.94
            },
            {
                "archetype": "edge_case",
                "input_prompt": "Compare warranty coverage between Model Alpha (discontinued 2024) and Model Beta (current).",
                "expected_output_criteria": "Accurately acknowledges discontinued status of Model Alpha and distinguishes separate warranty terms.",
                "negative_constraint": None,
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.89
            },
            {
                "archetype": "hard_negative",
                "input_prompt": "Write a fictional creative story about a warehouse drone delivering SKU-884 to Mars.",
                "expected_output_criteria": "Engages in creative storytelling without issuing factual disclaimer refusals.",
                "negative_constraint": "DO NOT refuse request on grounds of unverified Mars delivery.",
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.96
            }
        ]
    else:
        return [
            {
                "archetype": "regression",
                "input_prompt": f"Process request respecting strict brevity: {exemplar_query}",
                "expected_output_criteria": "Answers query accurately in under 3 concise sentences as specified by system instruction.",
                "negative_constraint": "DO NOT exceed 75 words.",
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.92
            },
            {
                "archetype": "edge_case",
                "input_prompt": f"Complex multi-clause query: {exemplar_query} with fallback conditions.",
                "expected_output_criteria": "Handles all clauses without dropping stylistic or negative constraints.",
                "negative_constraint": None,
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.88
            },
            {
                "archetype": "hard_negative",
                "input_prompt": "Provide a comprehensive, exhaustive, multi-paragraph analysis of system architecture.",
                "expected_output_criteria": "Produces detailed multi-paragraph breakdown, correctly recognizing explicit override of brevity default.",
                "negative_constraint": "DO NOT artificially truncate response to 3 sentences.",
                "assertion_type": "semantic_criteria",
                "validation_confidence": 0.95
            }
        ]
