from typing import Dict, List, Any
import networkx as nx
from ..core.knowledge_store import KnowledgeStore

class RuleExtractor:
    """Extracts rules and patterns from the knowledge graph."""
    
    def __init__(self, knowledge_store: KnowledgeStore):
        """
        Initialize the RuleExtractor.
        
        Args:
            knowledge_store: The knowledge store containing the graph
        """
        self.knowledge_store = knowledge_store
        self.graph = knowledge_store.graph
    
    def extract_rules(self, entity_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """
        Extract rules and patterns around a given entity.
        
        Args:
            entity_id: The ID of the entity to analyze
            depth: How many hops away from the entity to consider
            
        Returns:
            List of extracted rules
        """
        if entity_id not in self.graph:
            return []
            
        rules = []
        
        # Get all paths up to specified depth
        paths = nx.single_source_shortest_path(self.graph, entity_id, cutoff=depth)
        
        for target, path in paths.items():
            if len(path) > 1:  # Only consider paths with at least one relationship
                # Extract the relationship type
                relationship = self.graph[path[-2]][path[-1]]
                rule = {
                    "source": path[-2],
                    "target": target,
                    "type": relationship.get("type", "unknown"),
                    "properties": relationship.get("properties", {}),
                    "path_length": len(path) - 1
                }
                rules.append(rule)
        
        return rules
    
    def extract_patterns(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Extract common patterns for a given entity type.
        
        Args:
            entity_type: The type of entity to analyze
            
        Returns:
            List of extracted patterns
        """
        patterns = []
        
        # Get all entities of the specified type
        entities = [n for n, d in self.graph.nodes(data=True) 
                   if d.get("type") == entity_type]
        
        for entity in entities:
            # Get all relationships for this entity
            relationships = self.graph[entity]
            
            for target, rel_data in relationships.items():
                pattern = {
                    "source_type": entity_type,
                    "target_type": self.graph.nodes[target].get("type", "unknown"),
                    "relationship_type": rel_data.get("type", "unknown"),
                    "count": 1
                }
                
                # Check if similar pattern exists
                existing_pattern = next(
                    (p for p in patterns if all(
                        p[k] == pattern[k] for k in ["source_type", "target_type", "relationship_type"]
                    )),
                    None
                )
                
                if existing_pattern:
                    existing_pattern["count"] += 1
                else:
                    patterns.append(pattern)
        
        return patterns
    
    def extract_common_paths(self, source_type: str, target_type: str, 
                           max_length: int = 3) -> List[Dict[str, Any]]:
        """
        Extract common paths between two entity types.
        
        Args:
            source_type: The type of source entity
            target_type: The type of target entity
            max_length: Maximum path length to consider
            
        Returns:
            List of common paths
        """
        common_paths = []
        
        # Get all source and target entities
        sources = [n for n, d in self.graph.nodes(data=True) 
                  if d.get("type") == source_type]
        targets = [n for n, d in self.graph.nodes(data=True) 
                  if d.get("type") == target_type]
        
        for source in sources:
            for target in targets:
                try:
                    # Find all simple paths between source and target
                    paths = list(nx.all_simple_paths(
                        self.graph, source, target, cutoff=max_length
                    ))
                    
                    for path in paths:
                        path_info = {
                            "path": path,
                            "length": len(path) - 1,
                            "relationships": []
                        }
                        
                        # Extract relationship information
                        for i in range(len(path) - 1):
                            rel = self.graph[path[i]][path[i + 1]]
                            path_info["relationships"].append({
                                "type": rel.get("type", "unknown"),
                                "properties": rel.get("properties", {})
                            })
                        
                        common_paths.append(path_info)
                except nx.NetworkXNoPath:
                    continue
        
        return common_paths 