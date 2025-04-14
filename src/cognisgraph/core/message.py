from typing import Dict, List, Any, Optional

class AIMessage:
    """Class representing a message from an AI agent."""
    
    def __init__(self, 
                 status: str,
                 message: str,
                 entities: Optional[List[Dict[str, Any]]] = None,
                 relationships: Optional[List[Dict[str, Any]]] = None,
                 data: Optional[Dict[str, Any]] = None):
        self.status = status
        self.message = message
        self.entities = entities or []
        self.relationships = relationships or []
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary format."""
        return {
            "status": self.status,
            "message": self.message,
            "entities": self.entities,
            "relationships": self.relationships,
            "data": self.data
        } 