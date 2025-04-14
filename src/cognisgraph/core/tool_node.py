"""Tool node implementation."""
from typing import List, Callable, Dict, Any
from langgraph.prebuilt import ToolNode as LangGraphToolNode
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

class CognisToolNode:
    """A node that executes a set of tools and returns the result as an AIMessage."""
    
    def __init__(self, tools: List[Callable]):
        """Initialize the tool node.
        
        Args:
            tools: List of tool functions to execute
        """
        self.tools = tools
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tools and return the result.
        
        Args:
            state: Current state of the graph
            
        Returns:
            Updated state with tool execution results
        """
        # Get the last message from the state
        messages = state.get("messages", [])
        if not messages:
            return state
            
        last_message = messages[-1]
        
        # Execute the tools
        result = state
        for tool in self.tools:
            result = tool(result)
        
        # Convert the result to an AIMessage
        if isinstance(result, dict):
            if "error" in result:
                messages = [AIMessage(content=str(result["error"]))]
            elif "result" in result:
                messages = [AIMessage(content=str(result["result"]))]
            result["messages"] = messages
                
        return result 