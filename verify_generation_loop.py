import sys
import json
from src.generation.self_correction_loop import SelfCorrectionLoop
from config.settings import validate_settings

def run():
    print("====================================================")
    print("      Project Chronos Generation Loop Verification   ")
    print("====================================================")
    
    missing = validate_settings()
    if missing:
        print("[ERROR] Missing required configuration parameters:")
        for var in missing:
            print(f"  - {var}")
        sys.exit(1)

    # Validate LLM connectivity
    from src.utils.llm_client import validate_llm_connectivity
    validate_llm_connectivity()


    print("[*] Initializing Self-Correction Generation Loop...")
    try:
        loop = SelfCorrectionLoop()
        print("[✓] Loop initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize loop: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 1. Normal run (Factual query)
    q1 = "What competitor was mentioned in the financial report?"
    print(f"\n================================================================================")
    print(f"TEST CASE 1: Standard Ingestion Run")
    print(f"Query: '{q1}'")
    print(f"================================================================================")
    try:
        res1 = loop.run(q1, force_irrelevant=False)
        print("\n--- FINAL METRICS (TEST 1) ---")
        print(json.dumps(res1, indent=2))
    except Exception as e:
        print(f"[ERROR] Run failed for Test 1: {e}")
        import traceback
        traceback.print_exc()

    # 2. Simulated self-correction run (Low confidence path forced)
    q2 = "What was the capital investment allocated by Chronos Corp as of Q2 2024?"
    print(f"\n================================================================================")
    print(f"TEST CASE 2: Self-Correction Loop Trigger (Forced Irrelevant Context)")
    print(f"Query: '{q2}'")
    print(f"================================================================================")
    try:
        res2 = loop.run(q2, force_irrelevant=True)
        print("\n--- FINAL METRICS (TEST 2) ---")
        print(json.dumps(res2, indent=2))
    except Exception as e:
        print(f"[ERROR] Run failed for Test 2: {e}")
        import traceback
        traceback.print_exc()

    print("\n====================================================")
    print("      Verification Pipeline Complete!               ")
    print("====================================================")

if __name__ == "__main__":
    run()
