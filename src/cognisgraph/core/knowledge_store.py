from typing import Dict, List, Any, Optional
import networkx as nx
from pydantic import BaseModel
import logging # Import logging

logger = logging.getLogger(__name__) # Initialize logger

class Entity(BaseModel):
    """Represents an entity node in the knowledge graph.
    
    Attributes:
        id: A unique identifier for the entity.
        type: The category or type of the entity (e.g., Person, Organization).
        properties: A dictionary of key-value pairs describing the entity's attributes.
    """
    id: str
    type: str
    properties: Dict[str, Any]

class Relationship(BaseModel):
    """Represents a directed relationship (edge) between two entities.
    
    Attributes:
        source: The ID of the source entity.
        target: The ID of the target entity.
        type: The type of the relationship (e.g., works_at, colleague_of).
        properties: A dictionary of key-value pairs describing the relationship's attributes.
    """
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class KnowledgeStore:
    """Manages the storage and retrieval of entities and relationships using NetworkX.
    
    Provides methods to add, retrieve, and manage graph components, including
    indexing for efficient lookups.
    """
    
    def __init__(self):
        """Initializes an empty knowledge store with a NetworkX DiGraph and indexes."""
        self.graph = nx.DiGraph()
        self.entity_index: Dict[str, Entity] = {}
        self.relationship_index: Dict[str, Relationship] = {}
    
    def add_entity(self, entity: Entity) -> bool:
        """Adds an entity to the knowledge graph and its index.

        Args:
            entity: The Entity object to add.

        Returns:
            True if the entity was added successfully, False otherwise.
        """
        if not isinstance(entity, Entity):
            logger.error(f"Attempted to add non-Entity object: {entity}")
            return False
        if entity.id in self.entity_index:
            logger.warning(f"Entity with ID '{entity.id}' already exists. Skipping addition.")
            return False # Or update logic? Decide policy.
        try:
            self.graph.add_node(
                entity.id,
                type=entity.type,
                properties=entity.properties
            )
            self.entity_index[entity.id] = entity
            logger.debug(f"Added entity: {entity.id}")
            return True
        except Exception as e:
            logger.error(f"Error adding entity '{entity.id}': {e}")
            return False
    
    def add_relationship(self, relationship: Relationship) -> bool:
        """Adds a relationship to the knowledge graph and its index.
        
        Generates a unique key for indexing based on source, type, and target.
        Ensures source and target entities exist before adding the edge.

        Args:
            relationship: The Relationship object to add.

        Returns:
            True if the relationship was added successfully, False otherwise.
        """
        if not isinstance(relationship, Relationship):
            logger.error(f"Attempted to add non-Relationship object: {relationship}")
            return False
        if relationship.source not in self.entity_index:
            logger.error(f"Source entity '{relationship.source}' not found for relationship.")
            return False
        if relationship.target not in self.entity_index:
            logger.error(f"Target entity '{relationship.target}' not found for relationship.")
            return False
            
        key = f"{relationship.source}_{relationship.type}_{relationship.target}"
        if key in self.relationship_index:
            logger.warning(f"Relationship '{key}' already exists. Skipping addition.")
            return False # Or update logic?
            
        try:
            self.graph.add_edge(
                relationship.source,
                relationship.target,
                type=relationship.type,
                properties=relationship.properties
            )
            # print(f"[DEBUG store.add_relationship] Adding key: '{key}' for source: '{relationship.source}', target: '{relationship.target}'") # REMOVE DEBUG
            self.relationship_index[key] = relationship
            logger.debug(f"Added relationship: {key}")
            return True
        except Exception as e:
            logger.error(f"Error adding relationship '{key}': {e}")
            return False
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieves an entity by its ID.

        Args:
            entity_id: The ID of the entity to retrieve.

        Returns:
            The Entity object if found, otherwise None.
        """
        return self.entity_index.get(entity_id)
    
    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Gets all relationships (incoming and outgoing) connected to an entity.

        Args:
            entity_id: The ID of the entity whose relationships are to be retrieved.

        Returns:
            A list of Relationship objects connected to the entity.
        """
        if entity_id not in self.entity_index:
            logger.warning(f"Attempted to get relationships for non-existent entity: {entity_id}")
            return []
            
        found_relationships = []
        # Iterate through the relationship index directly
        for rel in self.relationship_index.values():
            if rel.source == entity_id or rel.target == entity_id:
                found_relationships.append(rel)
        return found_relationships
        
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
