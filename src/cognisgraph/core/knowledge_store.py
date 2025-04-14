from typing import Dict, List, Any, Optional, Set
import networkx as nx
from pydantic import BaseModel
import logging # Import logging
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship

logger = logging.getLogger(__name__) # Initialize logger

class KnowledgeStore:
    """Stores and manages entities and relationships in a knowledge graph."""
    
    def __init__(self):
        """Initialize the knowledge store."""
        self.graph = nx.DiGraph()
        self.entity_index: Dict[str, Entity] = {}
        self.relationship_index: Dict[str, List[Relationship]] = {}
        logger.info("KnowledgeStore initialized with empty graph.")
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the knowledge store.
        
        Args:
            entity: The entity to add.
        """
        if not isinstance(entity, Entity):
            raise TypeError("entity must be an instance of Entity")
            
        self.entity_index[entity.id] = entity
        # Add node to graph with entity properties and type
        node_attrs = {"type": entity.type}
        node_attrs.update(entity.properties)
        self.graph.add_node(entity.id, **node_attrs)
        logger.debug(f"Added entity: {entity.id}")
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the knowledge store.
        
        Args:
            relationship: The relationship to add.
        """
        if not isinstance(relationship, Relationship):
            raise TypeError("relationship must be an instance of Relationship")
            
        # Add relationship to index
        if relationship.source not in self.relationship_index:
            self.relationship_index[relationship.source] = []
        self.relationship_index[relationship.source].append(relationship)
        
        # Add edge to graph with relationship properties
        self.graph.add_edge(
            relationship.source,
            relationship.target,
            **relationship.properties
        )
        logger.debug(f"Added relationship: {relationship.source} -> {relationship.target}")
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID.
        
        Args:
            entity_id: The ID of the entity to retrieve.
            
        Returns:
            The entity if found, None otherwise.
        """
        return self.entity_index.get(entity_id)
    
    def get_entities(self) -> List[Entity]:
        """Get all entities in the knowledge store.
        
        Returns:
            A list of all entities.
        """
        return list(self.entity_index.values())
    
    def get_relationships(self, source_id: Optional[str] = None) -> List[Relationship]:
        """Get relationships from the knowledge store.
        
        Args:
            source_id: Optional source entity ID to filter relationships.
            
        Returns:
            A list of relationships.
        """
        if source_id is None:
            relationships = []
            for rel_list in self.relationship_index.values():
                relationships.extend(rel_list)
            return relationships
        return self.relationship_index.get(source_id, [])
    
    def has_entity(self, entity_id: str) -> bool:
        """Check if an entity exists in the knowledge store.
        
        Args:
            entity_id: The ID of the entity to check.
            
        Returns:
            True if the entity exists, False otherwise.
        """
        return entity_id in self.entity_index
    
    def has_relationship(self, source_id: str, target_id: str) -> bool:
        """Check if a relationship exists in the knowledge store.
        
        Args:
            source_id: The source entity ID.
            target_id: The target entity ID.
            
        Returns:
            True if the relationship exists, False otherwise.
        """
        return self.graph.has_edge(source_id, target_id)
    
    def clear(self) -> None:
        """Clear all entities and relationships from the knowledge store."""
        self.graph = nx.DiGraph()
        self.entity_index.clear()
        self.relationship_index.clear()
        logger.info("KnowledgeStore cleared.")

    def search_entities(self, query: str, top_k: int = 5) -> List[Entity]:
        """Searches for entities based on a simple text query (placeholder).
        
        Args:
            query: The text query string.
            top_k: The maximum number of entities to return.
            
        Returns:
            A list of matching Entity objects.
        """
        # Placeholder simple search - needs embedding-based search from QueryEngine
        results = []
        query_lower = query.lower()
        for entity in self.entity_index.values():
            entity_text = entity.properties.get('text', entity.id).lower()
            if query_lower in entity_text:
                results.append(entity)
            elif query_lower in entity.type.lower():
                results.append(entity)
            if len(results) >= top_k:
                break
        return results

    def get_graph(self) -> nx.DiGraph:
        """Returns the underlying NetworkX graph.
        
        Returns:
            The NetworkX DiGraph representing the knowledge graph.
        """
        return self.graph
        
    def add_knowledge(self, knowledge: Dict[str, Any]) -> bool:
        """Add knowledge to the store.
        
        Args:
            knowledge: A dictionary containing entity and relationship information
            
        Returns:
            True if the knowledge was added successfully, False otherwise
        """
        try:
            # Add entity
            entity = Entity(
                id=knowledge["entity"],
                type=knowledge["type"],
                properties=knowledge.get("properties", {})
            )
            if not self.add_entity(entity):
                return False
                
            # Add relationships if present
            if "relationships" in knowledge:
                for rel in knowledge["relationships"]:
                    relationship = Relationship(
                        source=knowledge["entity"],
                        target=rel["target"],
                        type=rel["type"],
                        properties=rel.get("properties", {})
                    )
                    if not self.add_relationship(relationship):
                        return False
                        
            return True
        except Exception as e:
            logger.error(f"Error adding knowledge: {str(e)}")
            return False
