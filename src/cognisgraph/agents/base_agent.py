from typing import Any, Dict, Optional, TypeVar, Generic
import logging
from abc import ABC, abstractmethod
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine
from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseAgent(ABC, Generic[T]):
    """Base class for all specialized agents in the system."""
    
    def __init__(
        self,
        knowledge_store: Optional[KnowledgeStore] = None,
        query_engine: Optional[QueryEngine] = None
    ):
        """Initialize the base agent.
        
        Args:
            knowledge_store: Optional shared knowledge store instance
            query_engine: Optional query engine instance
        """
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.query_engine = query_engine or QueryEngine()
        self.context: Dict[str, Any] = {}
        self.state_graph = StateGraph(dict)
        self.logger = logging.getLogger(self.__class__.__name__)
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    async def process(self, input_data: T) -> Dict[str, Any]:
        """Process input data asynchronously.
        
        Args:
            input_data: The input data to process
            
        Returns:
            Dict containing processing results
        """
        pass
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current context of the agent."""
        return self.context
    
    def reset(self) -> None:
        """Reset the agent's context."""
        self.context.clear()
        logger.info(f"{self.__class__.__name__} context reset")
    
    def update_context(self, key: str, value: Any) -> None:
        """Update the agent's context with new information.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        logger.debug(f"{self.__class__.__name__} context updated with {key}") 