from src.graph.neo4j_client import Neo4jGraphStore

class GraphSearcher:
    def __init__(self):
        pass

    def search(self, entities: list[str]) -> list[dict]:
        """Queries Neo4j for relationships connected to the list of entities."""
        if not entities:
            return []
            
        results = []
        try:
            with Neo4jGraphStore() as graph_store:
                for entity in entities:
                    paths = graph_store.get_relationship_paths(entity, max_depth=2)
                    for path in paths:
                        # Convert paths into structured candidates or documents
                        nodes_str = " -> ".join([f"{n['name']} ({n['type']})" for n in path["nodes"]])
                        rels_str = ", ".join([r["type"] for r in path["relationships"]])
                        path_text = f"Knowledge Graph Path: {nodes_str} | Relationships: [{rels_str}]"
                        
                        # Gather properties
                        rel_props = {}
                        for r in path["relationships"]:
                            rel_props.update(r.get("properties", {}))
                            
                        results.append({
                            "id": f"graph_{entity}_{rels_str}",
                            "text": path_text,
                            "metadata": {
                                "source_entity": entity,
                                "nodes": path["nodes"],
                                "relationships": path["relationships"],
                                "quarter": rel_props.get("quarter", ""),
                                "date": rel_props.get("date", "")
                            },
                            "score": 0.8,
                            "source": "graph"
                        })
        except Exception as e:
            print(f"[WARNING] Graph search failed: {e}")
            
        return results
