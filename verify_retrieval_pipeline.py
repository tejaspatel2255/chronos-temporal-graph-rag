import sys
from src.retrieval.retrieval_pipeline import RetrievalPipeline
from config.settings import validate_settings

def run():
    print("====================================================")
    print("      Project Chronos Retrieval Verification        ")
    print("====================================================")
    
    missing = validate_settings()
    if missing:
        print("[ERROR] Missing required configuration parameters:")
        for var in missing:
            print(f"  - {var}")
        sys.exit(1)

    print("[*] Initializing Retrieval Pipeline (downloading CrossEncoder model if needed)...")
    try:
        pipeline = RetrievalPipeline()
        print("[✓] Pipeline initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize pipeline: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    queries = [
        "What competitor was mentioned in the financial report?", # Factual
        "Compare Chronos Corp's R&D capital investment to Apex Data Systems.", # Analytical
        "What was the capital investment allocated by Chronos Corp as of Q2 2024?" # Temporal
    ]

    for idx, query in enumerate(queries):
        print("\n" + "="*80)
        print(f"QUERY {idx + 1}: '{query}'")
        print("="*80)
        
        try:
            output = pipeline.run(query)
            analysis = output["analysis"]
            results = output["results"]
            
            print("\n--- QUERY ANALYSIS ---")
            print(f"Classifications:   {analysis.get('classification')}")
            print(f"Entities:          {analysis.get('entities')}")
            print(f"Timeframe:         '{analysis.get('timeframe')}'")
            print(f"Metrics:           {analysis.get('metrics')}")
            print(f"Paraphrases:       {analysis.get('paraphrased_queries')}")
            
            print("\n--- TOP 5 RETRIEVED CHUNKS ---")
            if not results:
                print("[!] No matching results retrieved.")
            else:
                for rank, res in enumerate(results):
                    print(f"\n[Rank {rank + 1}] Source: {res['source'].upper()} | Score: {res['score']:.4f}")
                    orig_scores_str = ", ".join([f"{src}: {score:.4f}" for src, score in res.get('original_scores', {}).items()])
                    if orig_scores_str:
                        print(f"  (Original Rank Scores: {orig_scores_str})")
                    if res['source'] == 'structured':
                        print(f"  Row Data: {res['metadata'].get('row_data')}")
                    elif res['source'] == 'graph':
                        print(f"  Graph Path Info: {res['text']}")
                    else:
                        snippet = res['text'].replace('\n', ' ').strip()
                        if len(snippet) > 160:
                            snippet = snippet[:157] + "..."
                        print(f"  Text: \"{snippet}\"")
                        print(f"  Metadata: {res['metadata']}")
                        
        except Exception as e:
            print(f"[ERROR] Failed to run query retrieval: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("         Retrieval Verification Completed!          ")
    print("="*80)

if __name__ == "__main__":
    run()
