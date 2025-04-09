from typing import Dict, Any, List, Optional
from langgraph.graph import Graph, StateGraph
from .knowledge_store import KnowledgeStore
from .query_engine import QueryEngine

class CognisGraphWorkflow:
    """LangGraph-based workflow for CognisGraph operations."""
    
    def __init__(self, knowledge_store: KnowledgeStore, query_engine: QueryEngine):
        self.knowledge_store = knowledge_store
        self.query_engine = query_engine
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> Graph:
        """Create the LangGraph workflow."""
        # Create the graph
        workflow = StateGraph(dict)
        
        # Define nodes
        def add_knowledge(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node for adding knowledge to the graph."""
            if "current_knowledge" in state:
                knowledge = state["current_knowledge"]
                self.knowledge_store.add_entity(knowledge)
                if "knowledge" not in state:
                    state["knowledge"] = []
                state["knowledge"].append(knowledge)
            return state
        
        def process_query(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node for processing queries."""
            if "current_query" in state:
                query = state["current_query"]
                result = self.query_engine.process_query(query)
                if "results" not in state:
                    state["results"] = []
                state["results"].append(result)
            return state
        
        def visualize_graph(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node for visualizing the knowledge graph."""
            # This will be implemented in the visualization module
            return state
        
        # Add nodes to the graph
        workflow.add_node("add_knowledge", add_knowledge)
        workflow.add_node("process_query", process_query)
        workflow.add_node("visualize", visualize_graph)
        
        # Define edges
        workflow.add_edge("add_knowledge", "process_query")
        workflow.add_edge("process_query", "visualize")
        
        # Set entry point
        workflow.set_entry_point("add_knowledge")
        
        return workflow.compile()
    
    def run(self, knowledge: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Run the workflow with given knowledge and query."""
        # Create initial state
        initial_state = {
            "knowledge": [],
            "queries": [],
            "results": [],
            "current_knowledge": knowledge,
            "current_query": query
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        return final_state 