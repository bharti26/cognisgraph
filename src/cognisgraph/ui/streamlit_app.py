"""Streamlit application module."""
import streamlit as st
from typing import Dict, Any, Optional
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine
from cognisgraph.agents.orchestrator import OrchestratorAgent
from cognisgraph.visualization.graph_visualizer import GraphVisualizer
from cognisgraph.core.state_graph import create_graph
from cognisgraph.utils.logger import get_logger

logger = get_logger(__name__)

class StreamlitApp:
    """Streamlit application for CognisGraph."""
    
    def __init__(
        self,
        knowledge_store: Optional[KnowledgeStore] = None,
        query_engine: Optional[QueryEngine] = None,
        orchestrator: Optional[OrchestratorAgent] = None
    ):
        """Initialize the Streamlit application.
        
        Args:
            knowledge_store: Optional knowledge store instance
            query_engine: Optional query engine instance
            orchestrator: Optional orchestrator instance
        """
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.query_engine = query_engine or QueryEngine()
        self.orchestrator = orchestrator or OrchestratorAgent(self.knowledge_store)
        self.visualizer = GraphVisualizer(self.knowledge_store.graph)
        self.state_graph = create_graph()
        logger.info("StreamlitApp initialized")
    
    def run(self):
        """Run the Streamlit application."""
        st.title("CognisGraph")
        
        # Sidebar
        with st.sidebar:
            st.header("Controls")
            if st.button("Reset"):
                self.reset()
                st.success("Reset successful")
        
        # Main content
        st.header("Knowledge Graph Explorer")
        
        # File upload
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_file:
            self._handle_file_upload(uploaded_file)
        
        # Query input
        query = st.text_input("Enter your query")
        if query:
            self._handle_query(query)
    
    def _handle_file_upload(self, file):
        """Handle PDF file upload.
        
        Args:
            file: The uploaded file
        """
        try:
            result = self.orchestrator.process(file)
            if result["success"]:
                st.success("PDF processed successfully")
                if "visualization" in result:
                    st.plotly_chart(result["visualization"])
            else:
                st.error(f"Error processing PDF: {result.get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _handle_query(self, query: str):
        """Handle user query.
        
        Args:
            query: The user's query
        """
        try:
            result = self.orchestrator.process(query)
            if "error" not in result:
                st.write(result["results"])
                if "visualization" in result:
                    st.plotly_chart(result["visualization"])
            else:
                st.error(f"Error processing query: {result['error']}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def reset(self):
        """Reset the application state."""
        self.orchestrator.reset_all()
        logger.info("Application state reset")

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query and return the results.
        
        Args:
            query: The query to process
            
        Returns:
            A dictionary containing the query results
        """
        if not query:
            raise ValueError("Query cannot be empty")
            
        try:
            result = self.query_engine.execute_query(query, self.knowledge_store)
            if result["status"] == "success":
                # Generate visualization for query results
                visualization = self.visualizer.plot()
                result["visualization"] = visualization
            return result
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise 