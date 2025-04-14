"""Main CognisGraph application module."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import logging

from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship
from cognisgraph.agents.query_agent import QueryAgent
from cognisgraph.agents.visualization_agent import VisualizationAgent
from cognisgraph.agents.orchestrator import OrchestratorAgent
from cognisgraph.nlp.query_engine import QueryEngine
from cognisgraph.utils.logger import get_logger, CognisGraphLogger

@dataclass
class VisualizationConfig:
    """Configuration for visualization settings."""
    default_method: str = "plotly"

@dataclass
class Config:
    """Configuration for CognisGraph."""
    debug: bool = False
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    log_level: str = "INFO"

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return getattr(self, key, default)

    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> 'Config':
        """Create a Config instance from a dictionary.
        
        Args:
            config_dict: Optional configuration dictionary
            
        Returns:
            Config instance
        """
        if not config_dict:
            return cls()
            
        vis_config = VisualizationConfig(
            default_method=config_dict.get("visualization", {}).get("default_method", "plotly")
        )
        return cls(
            debug=config_dict.get("debug", False),
            visualization=vis_config,
            log_level=config_dict.get("log_level", "INFO")
        )

logger = CognisGraphLogger(__name__)

class CognisGraph:
    """Main CognisGraph class that orchestrates all components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CognisGraph.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = Config.from_dict(config)
        self.logger = logger
        self.logger.setLevel(self.config.log_level)
        
        # Initialize core components
        self.knowledge_store = KnowledgeStore()
        self.query_engine = QueryEngine(self.knowledge_store)
        
        # Initialize agents
        self.query_agent = QueryAgent(
            knowledge_store=self.knowledge_store,
            query_engine=self.query_engine
        )
        self.visualization_agent = VisualizationAgent(
            knowledge_store=self.knowledge_store,
            query_engine=self.query_engine
        )
        self.orchestrator = OrchestratorAgent(self.knowledge_store, self.query_engine)
        
        if self.config.debug:
            self.logger.setLevel("DEBUG")
            self.logger.debug("Debug mode enabled")
        
        self.logger.info("CognisGraph initialized successfully")
    
    async def add_knowledge(self, pdf_path: str) -> Dict[str, Any]:
        """Add knowledge from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing processing results
        """
        try:
            result = await self.orchestrator.process({
                "type": "pdf",
                "content": pdf_path
            })
            if result["status"] == "error":
                self.logger.error(f"Failed to process PDF: {result.get('message', 'Unknown error')}")
            else:
                self.logger.info(f"Successfully processed PDF: {pdf_path}")
            return result
        except Exception as e:
            error_msg = f"Error adding knowledge: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    async def query(self, query: str) -> Dict[str, Any]:
        """Execute a query against the knowledge store.
        
        Args:
            query: The query string
            
        Returns:
            Dict containing query results
        """
        try:
            result = await self.orchestrator.process({
                "type": "query",
                "content": query
            })
            if result["status"] == "error":
                self.logger.error(f"Query failed: {result['error']}")
            else:
                self.logger.info(f"Query executed successfully: {query}")
            return result
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    async def visualize(self, method: str = "plotly", output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate a visualization of the knowledge graph.
        
        Args:
            method: Visualization method ("plotly", "pyvis", or "graphviz")
            output_path: Optional path to save the visualization
            
        Returns:
            Dict containing visualization results
        """
        try:
            result = await self.orchestrator.process({
                "type": "visualization",
                "method": method,
                "output_path": output_path
            })
            
            if result["status"] == "error":
                self.logger.error(f"Visualization failed: {result['error']}")
            else:
                self.logger.info(f"Visualization generated successfully using {method}")
                
            return result
        except Exception as e:
            error_msg = f"Error generating visualization: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity from the knowledge store.
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            Optional[Entity]: The entity if found, None otherwise
        """
        return self.knowledge_store.get_entity(entity_id)
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all entities from the knowledge store.
        
        Returns:
            List of entity dictionaries
        """
        return self.knowledge_store.get_entities()
    
    def get_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships from the knowledge store.
        
        Returns:
            List of relationship dictionaries
        """
        return self.knowledge_store.get_relationships()
    
    async def run_workflow(self, knowledge: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Run a complete workflow: add knowledge and execute a query.
        
        Args:
            knowledge: Knowledge to add (e.g., PDF path)
            query: Query to execute
            
        Returns:
            Dict containing workflow results
        """
        try:
            # Add knowledge
            add_result = await self.add_knowledge(knowledge)
            if add_result["status"] == "error":
                return add_result
            
            # Execute query
            query_result = await self.query(query)
            return query_result
        except Exception as e:
            error_msg = f"Error running workflow: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            } 