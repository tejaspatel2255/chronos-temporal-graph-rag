import re
from neo4j import GraphDatabase
from config.settings import settings

class Neo4jGraphStore:
    def __init__(self):
        uri = settings.NEO4J_URI
        user = settings.NEO4J_USERNAME
        password = settings.NEO4J_PASSWORD
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        # Verify connectivity
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_entity_node(self, name: str, type: str, properties: dict = None):
        """Creates or updates an entity node in Neo4j using MERGE."""
        if properties is None:
            properties = {}
        
        # Merge properties
        props = {**properties, "name": name, "type": type}
        
        # Sanitize label name to prevent Cypher injection
        clean_type = re.sub(r'[^a-zA-Z0-9_]', '', type)
        
        query = (
            f"MERGE (n:Entity:{clean_type} {{name: $name}}) "
            "SET n += $properties "
            "RETURN n"
        )
        
        with self.driver.session() as session:
            session.run(query, name=name, properties=props)

    def create_relationship(self, from_name: str, to_name: str, rel_type: str, properties: dict = None):
        """Creates or updates a relationship between two entities using MERGE."""
        if properties is None:
            properties = {}
            
        clean_rel_type = re.sub(r'[^a-zA-Z0-9_]', '', rel_type).upper()
        
        query = (
            "MERGE (a:Entity {name: $from_name}) "
            "MERGE (b:Entity {name: $to_name}) "
            f"MERGE (a)-[r:{clean_rel_type}]->(b) "
            "SET r += $properties "
            "RETURN r"
        )
        
        with self.driver.session() as session:
            session.run(query, from_name=from_name, to_name=to_name, properties=properties)

    def get_relationship_paths(self, entity_name: str, max_depth: int = 3):
        """Finds paths connected to the given entity up to max_depth."""
        depth = min(max(1, int(max_depth)), 5)
        
        query = (
            f"MATCH path = (a:Entity {{name: $entity_name}})-[*1..{depth}]-(b:Entity) "
            "RETURN path"
        )
        
        paths_list = []
        with self.driver.session() as session:
            result = session.run(query, entity_name=entity_name)
            for record in result:
                path = record["path"]
                nodes = [
                    {"name": n["name"], "labels": list(n.labels), "type": n.get("type")}
                    for n in path.nodes
                ]
                relationships = [
                    {"type": r.type, "properties": dict(r.items())}
                    for r in path.relationships
                ]
                paths_list.append({"nodes": nodes, "relationships": relationships})
        return paths_list
