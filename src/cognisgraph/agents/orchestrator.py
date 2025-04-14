from typing import Any, Dict, Optional
import logging
from cognisgraph.agents.base_agent import BaseAgent
from cognisgraph.agents.pdf_agent import PDFProcessingAgent
from cognisgraph.agents.query_agent import QueryAgent
from cognisgraph.agents.visualization_agent import VisualizationAgent
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """Agent responsible for orchestrating between specialized agents."""
    
    def __init__(self, knowledge_store: KnowledgeStore, query_engine: QueryEngine, pdf_agent: Optional[PDFProcessingAgent] = None):
        """Initialize the orchestrator agent.
        
        Args:
            knowledge_store: Shared knowledge store instance
            query_engine: Query engine instance
            pdf_agent: Optional PDF processing agent instance. If not provided, one will be created.
        """
        super().__init__(knowledge_store)
        
        # Initialize specialized agents
        self.pdf_agent = pdf_agent or PDFProcessingAgent(knowledge_store=knowledge_store, llm=query_engine.llm)
        self.query_agent = QueryAgent(knowledge_store, query_engine)
        self.visualization_agent = VisualizationAgent(knowledge_store)
        
        logger.info("OrchestratorAgent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data using the appropriate agent.
        
        Args:
            input_data: Input data containing type and content
            
        Returns:
            Dict containing processing results
        """
        try:
            input_type = input_data.get("type")
            if input_type == "pdf":
                pdf_path = input_data.get("content")
                if not pdf_path:
                    return {
                        "status": "error",
                        "message": "No PDF path provided",
                        "data": None
                    }
                return await self.process_pdf(pdf_path)
            elif input_type == "query":
                query = input_data.get("content")
                if not query:
                    return {
                        "status": "error",
                        "message": "No query provided",
                        "data": None
                    }
                return await self.query_agent.process(query)
            elif input_type == "visualization":
                return await self.visualization_agent.process(input_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown input type: {input_type}",
                    "data": None
                }
        except Exception as e:
            error_msg = f"Error processing input: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "data": None
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get the status of all specialized agents.
        
        Returns:
            Dict containing status information for each agent
        """
        return {
            "pdf_agent": {
                "context": self.pdf_agent.get_context(),
                "status": "active"
            },
            "query_agent": {
                "context": self.query_agent.get_context(),
                "status": "active"
            },
            "visualization_agent": {
                "context": self.visualization_agent.get_context(),
                "status": "active"
            }
        }
    
    def reset_all(self) -> None:
        """Reset all specialized agents."""
        self.pdf_agent.reset()
        self.query_agent.reset()
        self.visualization_agent.reset()
        self.reset()
        logger.info("All agents reset")

    async def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a PDF file using the PDF processing agent.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing processing results with status and error/data
        """
        try:
            # Process PDF
            pdf_result = await self.pdf_agent.process(pdf_path)
            if pdf_result["status"] != "success":
                return pdf_result
            
            # Generate visualization
            viz_input = {
                "entities": self.knowledge_store.get_entities(),
                "relationships": self.knowledge_store.get_relationships()
            }
            viz_result = await self.visualization_agent.process(viz_input)
            
            # Combine results
            if viz_result["status"] == "success":
                return {
                    "status": "success",
                    "data": {
                        **pdf_result["data"],
                        "visualization": viz_result["data"]["figure"],
                        "graph_info": viz_result["data"]["graph_info"],
                        "pdf_path": pdf_path
                    }
                }
            else:
                return viz_result
                
        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "data": None
            } 