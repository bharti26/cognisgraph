import pytest
from unittest.mock import Mock, MagicMock
from cognisgraph.core.tool_node import CognisToolNode
from langchain_core.messages import AIMessage
from typing import Dict, Any, List

def test_tool_node_initialization():
    """Test tool node initialization."""
    def test_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Test tool function."""
        return state
    tools = [test_tool]
    node = CognisToolNode(tools)
    assert node.tools == tools

def test_tool_node_call():
    """Test tool node call method."""
    def test_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Test tool that returns a result."""
        return {"result": "test result"}
    
    tools = [test_tool]
    node = CognisToolNode(tools)
    
    state = {
        "messages": [AIMessage(content="test input")]
    }
    
    result = node(state)
    assert isinstance(result, dict)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert isinstance(result["messages"][0], AIMessage)
    assert result["messages"][0].content == "test result"

def test_tool_node_empty_messages():
    """Test tool node with empty messages."""
    def test_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Test tool that returns input state."""
        return state
    
    tools = [test_tool]
    node = CognisToolNode(tools)
    
    state = {
        "messages": []
    }
    
    result = node(state)
    assert result == state

def test_tool_node_multiple_tools():
    """Test tool node with multiple tools."""
    def tool1(state: Dict[str, Any]) -> Dict[str, Any]:
        """First test tool."""
        return {"result": "result1"}
    
    def tool2(state: Dict[str, Any]) -> Dict[str, Any]:
        """Second test tool."""
        return {"result": "result2"}
    
    tools = [tool1, tool2]
    node = CognisToolNode(tools)
    
    state = {
        "messages": [AIMessage(content="test input")]
    }
    
    result = node(state)
    assert isinstance(result, dict)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert isinstance(result["messages"][0], AIMessage)
    assert result["messages"][0].content == "result2"  # Last tool's result

def test_tool_node_error_handling():
    """Test tool node error handling."""
    def failing_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        """Test tool that raises an exception."""
        raise Exception("Test error")
    
    tools = [failing_tool]
    node = CognisToolNode(tools)
    
    state = {
        "messages": [AIMessage(content="test input")]
    }
    
    with pytest.raises(Exception) as exc_info:
        node(state)
    assert "Test error" in str(exc_info.value) 