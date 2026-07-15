import sys
import json
from src.workflow.runner import run_chronos_query
from config.settings import validate_settings

def run():
    print("====================================================")
    print("      Project Chronos Web Fallback Verification     ")
    print("====================================================")
    
    missing = validate_settings()
    if missing:
        print("[ERROR] Missing required configuration parameters:")
        for var in missing:
            print(f"  - {var}")
        sys.exit(1)

    # Question about 2026 which is not in our internal documents (will trigger fallback)
    query = "What is the capital allocation for Project Chronos in the year 2026?"
    
    print(f"\n[*] Running query: '{query}'")
    print("[*] Expecting: 2 query rewrites followed by a web search fallback...")
    
    try:
        result = run_chronos_query(query, force_fallback=True)
        print("\n=== CHRONOS RESPONSE ===")
        print(json.dumps(result, indent=2))
        
        # Verify the logs show web fallback ran
        attempts = result.get("attempts_log", [])
        web_ran = any("web_fallback" in str(att) or any(c.get("source") == "web" for c in result.get("context_used", [])) for att in attempts)
        
        print("\n=== VERIFICATION RESULTS ===")
        print(f"Total Retries Executed: {result.get('retries')}")
        print(f"Final Answer Grounding Valid: {result.get('is_valid')}")
        print(f"Final Answer Confidence Score: {result.get('confidence_score')}%")
        
        # Let's inspect context sources
        sources = [c.get("source") for c in result.get("context_used", [])]
        print(f"Context Sources Used: {sources}")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
