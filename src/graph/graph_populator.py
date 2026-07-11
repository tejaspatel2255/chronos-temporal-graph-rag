import time
from pathlib import Path
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import TextChunker
from src.utils.llm_client import LLMClient
from src.graph.entity_extractor import extract_entities, extract_relationships
from src.graph.neo4j_client import Neo4jGraphStore

class GraphPopulator:
    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.llm_client = LLMClient()
        
    def populate(self) -> dict:
        docs_dir = Path(__file__).parent.parent.parent / "data" / "documents"
        print(f"[*] Loading documents from: {docs_dir.resolve()}")
        docs = self.loader.load_directory(str(docs_dir))
        
        print(f"[*] Chunking {len(docs)} documents...")
        chunks = self.chunker.split_documents(docs)
        print(f"[✓] Created {len(chunks)} chunks.")
        
        entities_created = 0
        relationships_created = 0
        
        # Connect to Neo4j
        with Neo4jGraphStore() as graph_store:
            # Iterate and populate
            for idx, chunk in enumerate(chunks):
                print(f"[*] Processing chunk {idx + 1}/{len(chunks)}...")
                text = chunk.page_content
                doc_name = chunk.metadata.get("source", "unknown_doc")
                
                # Extract entities
                entities = extract_entities(text, self.llm_client)
                
                # Flatten entity categories into a single list
                flat_entities = []
                for entity_type, entity_list in entities.items():
                    for ent in entity_list:
                        # Standardize the type name (singular)
                        std_type = "Person"
                        if entity_type == "companies":
                            std_type = "Company"
                        elif entity_type == "products":
                            std_type = "Product"
                        elif entity_type == "events":
                            std_type = "Event"
                        elif entity_type == "metrics":
                            std_type = "Metric"
                        elif entity_type == "people":
                            std_type = "Person"
                            
                        flat_entities.append({
                            "name": ent.get("name"),
                            "type": std_type,
                            "context_snippet": ent.get("context_snippet", "")
                        })
                
                # Create a node for the source document itself
                doc_id = chunk.metadata.get("doc_id", "unknown")
                graph_store.create_entity_node(
                    name=doc_name,
                    type="Document",
                    properties={
                        "doc_id": doc_id,
                        "created_at": chunk.metadata.get("created_at", ""),
                        "modified_at": chunk.metadata.get("modified_at", "")
                    }
                )
                
                # Create entity nodes and link to the source document via MENTIONED_IN
                for ent in flat_entities:
                    if not ent["name"]:
                        continue
                    # Create the entity node
                    graph_store.create_entity_node(
                        name=ent["name"],
                        type=ent["type"],
                        properties={"context_snippet": ent["context_snippet"]}
                    )
                    entities_created += 1
                    
                    # Create MENTIONED_IN relationship from Entity to Document
                    graph_store.create_relationship(
                        from_name=ent["name"],
                        to_name=doc_name,
                        rel_type="MENTIONED_IN",
                        properties={
                            "chunk_index": chunk.metadata.get("chunk_index", 0),
                            "chunk_id": chunk.metadata.get("chunk_id", "")
                        }
                    )
                    relationships_created += 1
                
                # Extract relationships between entities in this chunk
                if flat_entities:
                    extracted_rels = extract_relationships(text, flat_entities, self.llm_client)
                    for rel in extracted_rels:
                        from_ent = rel.get("from_entity")
                        to_ent = rel.get("to_entity")
                        rel_type = rel.get("relationship_type")
                        
                        if not from_ent or not to_ent or not rel_type:
                            continue
                            
                        # Build properties
                        props = {}
                        if rel.get("date"):
                            props["date"] = rel.get("date")
                        if rel.get("quarter"):
                            props["quarter"] = rel.get("quarter")
                            
                        # Create relationship
                        graph_store.create_relationship(
                            from_name=from_ent,
                            to_name=to_ent,
                            rel_type=rel_type,
                            properties=props
                        )
                        relationships_created += 1
                        print(f"  [✓] Relationship: ({from_ent}) -[{rel_type}]-> ({to_ent})")
                
                # Wait 2 seconds to avoid rate limiting
                time.sleep(2)
                        
        return {
            "entities_created": entities_created,
            "relationships_created": relationships_created
        }
