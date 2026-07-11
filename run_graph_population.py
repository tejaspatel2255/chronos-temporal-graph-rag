import sys
from src.graph.graph_populator import GraphPopulator
from src.graph.neo4j_client import Neo4jGraphStore
from config.settings import settings, validate_settings

def run():
    print("====================================================")
    print("         Project Chronos Graph Population           ")
    print("====================================================")
    
    # Check settings
    missing = validate_settings()
    if missing:
        print("[ERROR] Missing required configuration parameters:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease update your .env file and try again.")
        sys.exit(1)
        
    if not settings.OPENROUTER_API_KEY:
        print("[ERROR] OPENROUTER_API_KEY is not set in .env. LLM calls will fail.")
        sys.exit(1)

    # 1. Run Graph Population Pipeline
    try:
        populator = GraphPopulator()
        results = populator.populate()
        
        print("\n====================================================")
        print("[SUCCESS] Graph population completed successfully!")
        print(f" - Approximate entities processed:      {results['entities_created']}")
        print(f" - Approximate relationships created:   {results['relationships_created']}")
        print("====================================================")
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline run failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 2. Verify with direct Cypher query
    print("\n[*] Verifying node labels in Neo4j database...")
    try:
        with Neo4jGraphStore() as graph_store:
            query = "MATCH (n) RETURN labels(n) AS labels, count(*) AS count"
            with graph_store.driver.session() as session:
                result = session.run(query)
                records = list(result)
                
                if not records:
                    print("[!] No nodes found in the database.")
                else:
                    print("Label distribution:")
                    for rec in records:
                        print(f" - Labels: {rec['labels']} | Count: {rec['count']}")
                        
    except Exception as e:
        print(f"[ERROR] Failed to run verification Cypher query: {e}")

    # 3. Print relationship paths for a sample entity
    sample_entities = ["Apex Data Systems", "Chronos Corp", "ChronosAnalyst"]
    print("\n[*] Fetching relationship paths for sample entities...")
    try:
        with Neo4jGraphStore() as graph_store:
            found_paths = False
            for entity in sample_entities:
                paths = graph_store.get_relationship_paths(entity, max_depth=2)
                if paths:
                    found_paths = True
                    print(f"\nRelationship paths for '{entity}':")
                    # Limit output to first 3 paths to keep it readable
                    for idx, path in enumerate(paths[:3]):
                        nodes_str = " -> ".join([f"{n['name']} ({n['type']})" for n in path["nodes"]])
                        rels_str = ", ".join([r["type"] for r in path["relationships"]])
                        print(f" Path {idx + 1}: {nodes_str} | Relationships: [{rels_str}]")
                    break
            
            if not found_paths:
                print("[!] No relationship paths found for the sample entities.")
                
    except Exception as e:
        print(f"[ERROR] Failed to fetch relationship paths: {e}")
        
    print("\n====================================================")

if __name__ == "__main__":
    run()
