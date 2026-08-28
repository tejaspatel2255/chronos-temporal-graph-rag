import re
from neo4j import GraphDatabase
from config.settings import settings

class Neo4jGraphStore:
    def __init__(self):
        uri = settings.NEO4J_URI.replace("localhost", "127.0.0.1")
        user = settings.NEO4J_USERNAME
        password = settings.NEO4J_PASSWORD
        
        self.is_connected = False
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.is_connected = True
        except Exception as e:
            print(f"[WARNING] Neo4j connection unavailable at {uri}: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_entity_node(self, name: str, type: str, properties: dict = None):
        """Creates or updates an entity node in Neo4j using MERGE."""
        if not self.is_connected or not self.driver:
            print(f"[WARNING] Neo4j offline. Skipping node creation for '{name}'.")
            return
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
        if not self.is_connected or not self.driver:
            return
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
        if not self.is_connected or not self.driver:
            return []
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

    def get_full_graph(self, limit: int = 150):
        """Returns all entity nodes and their relationships for visualization."""
        if not self.is_connected or not self.driver:
            return {"nodes": [], "relationships": []}
        nodes_query = (
            "MATCH (n:Entity) RETURN n.name AS name, n.type AS type, labels(n) AS labels "
            f"LIMIT {limit}"
        )
        edges_query = (
            "MATCH (a:Entity)-[r]->(b:Entity) "
            "RETURN a.name AS source, b.name AS target, type(r) AS rel_type, "
            "r.date AS date, r.quarter AS quarter "
            f"LIMIT {limit * 3}"
        )

        nodes = []
        links = []
        seen_nodes = set()

        with self.driver.session() as session:
            node_result = session.run(nodes_query)
            for record in node_result:
                name = record["name"]
                if name and name not in seen_nodes:
                    seen_nodes.add(name)
                    labels = [l for l in (record["labels"] or []) if l != "Entity"]
                    entity_type = record["type"] or (labels[0] if labels else "Unknown")
                    nodes.append({
                        "id": name,
                        "name": name,
                        "type": entity_type,
                        "labels": labels
                    })

            edge_result = session.run(edges_query)
            for record in edge_result:
                source = record["source"]
                target = record["target"]
                if source and target:
                    links.append({
                        "source": source,
                        "target": target,
                        "rel_type": record["rel_type"] or "RELATED_TO",
                        "date": record["date"],
        return {"nodes": nodes, "links": links}

    def get_temporal_events(self):
        """Retrieves all temporal entity events and dated relationships ordered chronologically."""
        query = (
            "MATCH (a:Entity)-[r]->(b:Entity) "
            "WHERE r.date IS NOT NULL OR r.quarter IS NOT NULL "
            "RETURN a.name AS source, a.type AS source_type, b.name AS target, b.type AS target_type, "
            "type(r) AS rel_type, r.date AS date, r.quarter AS quarter, r.description AS description "
            "ORDER BY coalesce(r.date, r.quarter) ASC"
        )
        events = []
        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                date_str = record["date"] or record["quarter"] or "Undated"
                events.append({
                    "source": record["source"],
                    "source_type": record["source_type"] or "Entity",
                    "target": record["target"],
                    "target_type": record["target_type"] or "Entity",
                    "rel_type": record["rel_type"] or "RELATED_TO",
                    "date": date_str,
                    "quarter": record["quarter"],
                    "description": record["description"] or f"{record['source']} {record['rel_type'].replace('_', ' ').lower()} {record['target']}"
                })
        return events


