"""State graph implementation."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from langchain_core.documents import Document

class CognisGraphInput(BaseModel):
    """Input for the state graph."""
    content: str = Field(..., description="The content to process (query or file path)")
    input_type: str = Field(..., description="Type of input (query or pdf)")
    context: Optional[str] = Field(None, description="Additional context")

class CognisGraphOutput(BaseModel):
    """Output from the state graph."""
    status: str = Field(..., description="Status of the operation")
    result: Optional[Any] = Field(None, description="Result of the operation")
    error: Optional[str] = Field(None, description="Error message if any")

class CognisGraphState(BaseModel):
    """State for the state graph."""
    messages: List[AIMessage] = Field(default_factory=list, description="Messages in the conversation")
    documents: List[Document] = Field(default_factory=list, description="Processed documents")
    result: Optional[Any] = Field(None, description="Result of the operation")

def create_graph(tools: List[Any] = None) -> StateGraph:
    """Create and configure a state graph.
    
    Args:
        tools: List of tools to use in the graph
        
    Returns:
        A configured StateGraph instance
    """
    # Create the graph with our state schema
    graph = StateGraph(CognisGraphState)
    
    # Add document processing node
    doc_node = ToolNode(tools=tools or [])
    graph.add_node("document_processor", doc_node)
    
    # Add tool execution node
    tool_node = ToolNode(tools=tools or [])
    graph.add_node("tool_executor", tool_node)
    
    # Add edges based on input type
    def router(state: Dict[str, Any]) -> str:
        """Route to the appropriate node based on input type."""
        if state.get("input_type") == "pdf":
            return "document_processor"
        return "tool_executor"
    
    # Add start node
    graph.add_node("start", lambda x: x)
    
    # Add end node
    graph.add_node("end", lambda x: x)
    
    # Set the entry point
    graph.set_entry_point("start")
    
    # Add routing logic
    graph.add_conditional_edges(
        "start",
        router,
        {
            "document_processor": "document_processor",
            "tool_executor": "tool_executor"
        }
    )
    
    # Add edges to end
    graph.add_edge("document_processor", "end")
    graph.add_edge("tool_executor", "end")
    
    return graph.compile()

def reset_graph(graph: StateGraph) -> None:
    """Reset the state graph.
    
    Args:
        graph: The state graph to reset
    """
    if hasattr(graph, "state"):
        graph.state = CognisGraphState()

__all__ = ['CognisGraphState', 'create_graph', 'reset_graph'] 