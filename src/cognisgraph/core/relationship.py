from typing import Dict, Any
from pydantic import BaseModel

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
    
    def __hash__(self):
        """Make Relationship hashable using its source, target, and type.
        
        Returns:
            Hash of the relationship's key attributes
        """
        return hash((self.source, self.target, self.type))
    
    def __eq__(self, other):
        """Define equality based on source, target, and type.
        
        Args:
            other: Another Relationship object
            
        Returns:
            True if the relationships have the same key attributes
        """
        if not isinstance(other, Relationship):
            return False
        return (self.source == other.source and 
                self.target == other.target and 
                self.type == other.type) 