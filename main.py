import argparse
import sys
import json
from config.settings import validate_settings
from src.workflow.runner import run_chronos_query

def main():
    missing = validate_settings()
    if missing:
        print("[ERROR] Missing required configuration parameters:")
        for var in missing:
            print(f"  - {var}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Chronos Self-Correcting Temporal Enterprise Analyst CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", type=str, help="Run a single query through the RAG pipeline.")
    group.add_argument("--interactive", action="store_true", help="Start an interactive session.")
    
    args = parser.parse_args()
    
    if args.query:
        print(f"[*] Executing query: '{args.query}'")
        result = run_chronos_query(args.query)
        print("\n=== CHRONOS RESPONSE ===")
        print(json.dumps(result, indent=2))
        
    elif args.interactive:
        print("======================================================================")
        print("          Project Chronos Interactive Mode (Type 'exit' to quit)     ")
        print("======================================================================")
        
        while True:
            try:
                query = input("\nChronos Analyst > ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit"]:
                    print("[*] Exiting interactive mode. Goodbye!")
                    break
                    
                print(f"[*] Running: '{query}'")
                result = run_chronos_query(query)
                print("\n=== CHRONOS RESPONSE ===")
                print(json.dumps(result, indent=2))
            except KeyboardInterrupt:
                print("\n[*] Exiting interactive mode. Goodbye!")
                break
            except Exception as e:
                print(f"[ERROR] Query failed: {e}")

if __name__ == "__main__":
    main()
