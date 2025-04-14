from typing import Dict, Any
from pydantic import BaseModel

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
    
    def __hash__(self):
        """Make Entity hashable using its id.
        
        Returns:
            Hash of the entity's id
        """
        return hash(self.id)
    
    def __eq__(self, other):
        """Define equality based on id.
        
        Args:
            other: Another Entity object
            
        Returns:
            True if the entities have the same id
        """
        if not isinstance(other, Entity):
            return False
        return self.id == other.id