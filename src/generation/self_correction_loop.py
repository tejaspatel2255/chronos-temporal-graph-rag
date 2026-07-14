import time
from src.utils.llm_client import LLMClient
from src.retrieval.retrieval_pipeline import RetrievalPipeline
from src.generation.generator import generate_draft
from src.generation.validator import validate_answer
from src.generation.corrector import rewrite_query

class SelfCorrectionLoop:
    def __init__(self):
        self.llm_client = LLMClient()
        self.retrieval_pipeline = RetrievalPipeline()

    def run(self, query: str, force_irrelevant: bool = False) -> dict:
        """Executes the generate-validate-correct loop up to 2 retries."""
        attempts = []
        current_query = query
        retries = 0
        max_retries = 2
        
        while retries <= max_retries:
            print(f"\n--- [Iteration {retries}] Query: '{current_query}' ---")
            
            # 1. Retrieval
            retrieval_output = self.retrieval_pipeline.run(current_query)
            context = retrieval_output["results"]
            
            # Artificial low confidence simulation (replacing with irrelevant context on 1st loop iteration)
            if force_irrelevant and retries == 0:
                print("[!] SIMULATING LOW-CONFIDENCE PATH: Overriding retrieved context with irrelevant content...")
                context = [{
                    "id": "irrelevant_chunk_999",
                    "text": "The price of tea in China has decreased by 12% in the last fiscal quarter.",
                    "metadata": {"source": "unrelated_news.txt"},
                    "score": 0.1,
                    "source": "vector"
                }]
            
            # 2. Generate Draft Answer
            print("[*] Generating draft answer...")
            draft = generate_draft(current_query, context, self.llm_client)
            
            # 3. Validate Answer
            print("[*] Validating draft answer...")
            validation = validate_answer(draft["answer"], context, self.llm_client)
            
            confidence = validation.get("confidence", 0)
            is_valid = confidence >= 70
            
            # Store attempt details
            attempt_record = {
                "query": current_query,
                "answer": draft["answer"],
                "citations": draft["raw_citations"],
                "validation": validation,
                "context_used": context,
                "confidence": confidence,
                "is_valid": is_valid
            }
            attempts.append(attempt_record)
            
            print(f"[✓] Validation Completed. Confidence: {confidence}% | Is Valid: {is_valid}")
            
            if is_valid:
                print("[✓] Answer is valid! Exiting loop.")
                break
                
            if retries < max_retries:
                print(f"[!] Confidence ({confidence}%) below threshold (70%). Rewriting query...")
                current_query = rewrite_query(current_query, validation, self.llm_client)
                print(f"[✓] Rewritten query: '{current_query}'")
                retries += 1
                # Sleep briefly to manage rate limits
                time.sleep(2)
            else:
                print("[!] Max retries reached. Selecting best answer from attempts.")
                break
                
        # Select best overall attempt based on confidence
        best_attempt = max(attempts, key=lambda x: x["confidence"])
        
        return {
            "answer": best_attempt["answer"],
            "confidence_score": best_attempt["confidence"],
            "is_valid": best_attempt["is_valid"],
            "retries": retries,
            "citations": best_attempt["citations"],
            "context_used": [
                {
                    "id": c.get("id"),
                    "source": c.get("metadata", {}).get("source", "unknown"),
                    "text": c.get("text")
                }
                for c in best_attempt["context_used"]
            ],
            "attempts_log": [
                {
                    "retry_index": idx,
                    "query_used": att["query"],
                    "confidence": att["confidence"],
                    "reasoning": att["validation"].get("reasoning", "")
                }
                for idx, att in enumerate(attempts)
            ]
        }
