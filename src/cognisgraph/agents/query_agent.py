from typing import Any, Dict, List, Optional
import logging
from cognisgraph.agents.base_agent import BaseAgent
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine
from cognisgraph.xai.explainer import GraphExplainer

logger = logging.getLogger(__name__)

class QueryAgent(BaseAgent[str]):
    """Agent responsible for processing queries and generating explanations."""
    
    def __init__(
        self,
        knowledge_store: Optional[KnowledgeStore] = None,
        query_engine: Optional[QueryEngine] = None
    ):
        """Initialize the query agent.
        
        Args:
            knowledge_store: Optional shared knowledge store instance
            query_engine: Optional query engine instance
        """
        super().__init__(knowledge_store, query_engine)
        self.explainer = GraphExplainer(self.knowledge_store)
        logger.info("QueryAgent initialized")
        logger.debug(f"Knowledge store initialized: {self.knowledge_store is not None}")
        logger.debug(f"Query engine initialized: {self.query_engine is not None}")
    
    async def process(self, input_data: str) -> Dict[str, Any]:
        """Process a query and return the result with explanation."""
        if not input_data or not input_data.strip():
            return {
                "status": "error",
                "message": "Empty query"
            }

        if not self.query_engine:
            return {
                "status": "error",
                "message": "No query engine available"
            }

        try:
            response = await self.query_engine.execute_query(input_data, self.knowledge_store)
            
            result = {
                "status": "success",
                "data": {
                    "result": response.get("answer", ""),
                    "answer": response.get("answer", ""),
                    "confidence": response.get("confidence", 0.0),
                    "explanation": response.get("explanation", ""),
                    "entities": response.get("entities", []),
                    "relationships": response.get("relationships", [])
                }
            }

            # Include XAI metrics if present
            if "xai_metrics" in response:
                result["data"]["xai_metrics"] = response["xai_metrics"]

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": "Error processing query"
            }
    
    def get_similar_queries(self, query: str, limit: int = 5) -> List[str]:
        """Get similar queries from the knowledge store.
        
        Args:
            query: The query to find similar queries for
            limit: Maximum number of similar queries to return
            
        Returns:
            List of similar queries
        """
        return self.knowledge_store.get_similar_queries(query, limit) 