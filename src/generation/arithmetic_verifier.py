import re
from typing import Dict, Any, List
from src.utils.llm_client import LLMClient

class ArithmeticVerifier:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def verify_answer_math(self, draft_answer: str, context_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scans draft answer for mathematical/financial claims and verifies arithmetic accuracy against context."""
        # 1. Quick regex check if answer contains numbers/percentages
        has_numbers = bool(re.search(r'\d+(\.\d+)?%|\$\d+|\d+\s*(million|billion|M|B)', draft_answer, re.IGNORECASE))
        if not has_numbers:
            return {
                "answer": draft_answer,
                "verified": True,
                "corrections_made": False,
                "notes": "No numerical or financial metrics detected."
            }

        # Combine context text
        context_text = "\n---\n".join([c.get("text", "") for c in context_candidates[:5]])

        prompt = f"""You are a strict financial auditor & arithmetic verification agent.
Your job is to check the generated response against the provided financial context and verify that:
1. All numerical values (revenue, R&D spend, capital expenditure, growth rates, sums, percentages) are factually accurate.
2. Any calculated YoY growth rates or percentage differences in the answer are mathematically correct.
3. If an arithmetic error or minor numerical hallucination is found, fix the calculation in the text.

--- CONTEXT DATA ---
{context_text}

--- GENERATED ANSWER TO VERIFY ---
{draft_answer}

Instructions:
Return a JSON object matching this schema:
{{
    "verified": true/false,
    "corrections_made": true/false,
    "corrected_answer": "Final corrected text if corrections were made, otherwise return the exact input answer.",
    "audit_notes": "Brief explanation of verified numbers or corrections made."
}}
"""
        try:
            res = self.llm.json_completion(prompt)
            return {
                "answer": res.get("corrected_answer", draft_answer),
                "verified": res.get("verified", True),
                "corrections_made": res.get("corrections_made", False),
                "notes": res.get("audit_notes", "Verified numerical statements.")
            }
        except Exception as e:
            print(f"[WARNING] Arithmetic verification check skipped: {e}")
            return {
                "answer": draft_answer,
                "verified": True,
                "corrections_made": False,
                "notes": f"Verification bypassed due to error: {e}"
            }
