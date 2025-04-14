import pytest
from unittest.mock import Mock
from langgraph.graph import StateGraph
from cognisgraph.agents.base_agent import BaseAgent
from cognisgraph.agents.query_agent import QueryAgent
from cognisgraph.agents.visualization_agent import VisualizationAgent
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine
from typing import Dict, Any
import networkx as nx
from unittest.mock import patch

class TestAgent(BaseAgent[str]):
    """A concrete test agent for testing purposes."""
    
    async def process(self, input_data: str) -> Dict[str, Any]:
        """Process input data."""
        return {
            "status": "success",
            "data": {
                "input": input_data,
                "result": f"Processed: {input_data}"
            }
        }

@pytest.fixture
def mock_knowledge_store():
    """Create a mock knowledge store."""
    store = Mock(spec=KnowledgeStore)
    graph = nx.DiGraph()
    graph.add_node("test_node")
    store.graph = graph
    store.get_graph.return_value = graph
    store.get_entity.return_value = None
    store.get_relationships.return_value = [
        {"source": "ent1", "target": "ent2", "type": "RELATED_TO", "properties": {"description": "Test relationship"}}
    ]
    store.get_entities.return_value = [
        {"id": "ent1", "type": "test", "properties": {"name": "Test Entity 1"}},
        {"id": "ent2", "type": "test", "properties": {"name": "Test Entity 2"}}
    ]
    return store

@pytest.fixture
def mock_query_engine():
    """Create a mock query engine."""
    engine = Mock(spec=QueryEngine)
    engine.execute_query.return_value = {
        "status": "success",
        "answer": "Test answer",
        "confidence": 0.95,
        "explanation": "Test explanation",
        "entities": [],  # Empty list instead of mock
        "relationships": []  # Empty list instead of mock
    }
    return engine

@pytest.fixture
def mock_explainer():
    """Create a mock explainer."""
    explainer = Mock()
    explainer.explain_query_result.return_value = "Test explanation"
    return explainer

@pytest.fixture
def test_agent(mock_knowledge_store, mock_query_engine):
    """Create a test agent instance."""
    return TestAgent(
        knowledge_store=mock_knowledge_store,
        query_engine=mock_query_engine
    )

@pytest.fixture
def query_agent(mock_knowledge_store, mock_query_engine):
    """Create a query agent instance."""
    agent = QueryAgent(mock_knowledge_store, mock_query_engine)
    # Ensure execute_query is called
    agent.query_engine.execute_query = mock_query_engine.execute_query
    return agent

@pytest.fixture
def visualization_agent(mock_knowledge_store):
    """Create a visualization agent instance."""
    return VisualizationAgent(mock_knowledge_store)

@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test base agent initialization."""
    agent = TestAgent()
    assert isinstance(agent.context, dict)
    assert agent.context == {}
    assert isinstance(agent.state_graph, StateGraph)

@pytest.mark.asyncio
async def test_base_agent_process(test_agent):
    """Test base agent process method."""
    result = await test_agent.process("test input")
    assert result["status"] == "success"
    assert "data" in result
    assert result["data"]["input"] == "test input"
    assert "Processed: test input" in result["data"]["result"]

def test_base_agent_context_management(test_agent):
    """Test base agent context management."""
    # Test context update
    test_agent.context["test_key"] = "test_value"
    assert test_agent.context["test_key"] == "test_value"
    
    # Test context retrieval
    context = test_agent.get_context()
    assert context == {"test_key": "test_value"}
    
    # Test context reset
    test_agent.reset()
    assert test_agent.context == {}

@pytest.mark.asyncio
async def test_query_agent_initialization(query_agent, mock_knowledge_store, mock_query_engine):
    """Test query agent initialization."""
    assert query_agent.knowledge_store == mock_knowledge_store
    assert query_agent.query_engine == mock_query_engine
    assert isinstance(query_agent.context, dict)
    assert query_agent.context == {}
    assert isinstance(query_agent.state_graph, StateGraph)

@pytest.mark.asyncio
async def test_query_agent_process(query_agent, mock_query_engine):
    """Test query agent process method."""
    query = "Test query"
    result = await query_agent.process(query)
    assert result["status"] == "success"
    assert "data" in result
    assert "result" in result["data"]
    assert "explanation" in result["data"]
    mock_query_engine.execute_query.assert_called_once_with(query, query_agent.knowledge_store)

@pytest.mark.asyncio
async def test_query_agent_error_handling(query_agent):
    """Test query agent error handling."""
    query_agent.query_engine = None
    result = await query_agent.process("test query")
    assert result["status"] == "error"
    assert "message" in result
    assert "No query engine available" in result["message"]

@pytest.mark.asyncio
async def test_query_agent_answer_generation(query_agent, mock_query_engine):
    """Test that the query agent generates a proper answer."""
    mock_query_engine.execute_query.return_value = {
        "status": "success",
        "result": "Paris is the capital of France",
        "answer": "Paris is the capital of France",
        "confidence": 0.95,
        "explanation": "Based on the knowledge graph data",
        "entities": [],
        "relationships": []
    }
    
    result = await query_agent.process("What is the capital of France?")
    
    assert result["status"] == "success"
    assert "data" in result
    assert "Paris" in result["data"]["result"]
    assert "France" in result["data"]["result"]
    assert "explanation" in result["data"]
    mock_query_engine.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_query_agent_empty_graph(query_agent, mock_query_engine):
    """Test that the query agent handles empty graph gracefully."""
    mock_query_engine.execute_query.return_value = {
        "status": "success",
        "result": "Based on general knowledge, Paris is the capital of France",
        "answer": "Based on general knowledge, Paris is the capital of France",
        "confidence": 0.8,
        "explanation": "No specific data in knowledge graph",
        "entities": [],
        "relationships": []
    }
    
    result = await query_agent.process("What is the capital of France?")
    
    assert result["status"] == "success"
    assert "data" in result
    assert "Paris" in result["data"]["result"]
    assert "France" in result["data"]["result"]
    assert "explanation" in result["data"]
    mock_query_engine.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_visualization_agent_initialization(visualization_agent, mock_knowledge_store):
    """Test visualization agent initialization."""
    assert visualization_agent.knowledge_store == mock_knowledge_store
    assert isinstance(visualization_agent.context, dict)
    assert visualization_agent.context == {}
    assert visualization_agent.visualizer is None
    assert isinstance(visualization_agent.state_graph, StateGraph)

@pytest.mark.asyncio
async def test_visualization_agent_process(visualization_agent, mock_knowledge_store):
    """Test visualization agent process method."""
    input_data = {
        "entities": [
            {"id": "ent1", "type": "test", "properties": {"name": "Test Entity 1"}},
            {"id": "ent2", "type": "test", "properties": {"name": "Test Entity 2"}}
        ],
        "relationships": [
            {"source": "ent1", "target": "ent2", "type": "RELATED_TO", "properties": {"description": "Test relationship"}}
        ]
    }
    result = await visualization_agent.process(input_data)
    assert result["status"] == "success"
    assert "data" in result
    assert "figure" in result["data"]
    assert "graph_info" in result["data"]

@pytest.mark.asyncio
async def test_visualization_agent_error_handling(visualization_agent):
    """Test visualization agent error handling."""
    visualization_agent.knowledge_store = None
    result = await visualization_agent.process({})
    assert result["status"] == "error"
    assert "No knowledge store available" in result["message"]

@pytest.mark.asyncio
async def test_query_agent_real_answer_generation(query_agent, mock_query_engine, mock_knowledge_store):
    """Test that the query agent generates a proper answer with real components."""
    # Initialize some entities and relationships in the knowledge store
    mock_knowledge_store.add_entity.return_value = True
    mock_knowledge_store.add_relationship.return_value = True
    
    mock_query_engine.execute_query.return_value = {
        "status": "success",
        "answer": "Test answer with real components",
        "confidence": 0.95,
        "explanation": "Test explanation",
        "entities": [{"id": "1", "type": "test", "properties": {}}],
        "relationships": [{"source": "1", "target": "2", "type": "test_rel"}]
    }

    result = await query_agent.process("Test query with real components")
    assert result["status"] == "success"
    assert "data" in result
    assert result["data"]["answer"] == "Test answer with real components"
    assert result["data"]["confidence"] == 0.95
    assert len(result["data"]["entities"]) == 1
    assert len(result["data"]["relationships"]) == 1

@pytest.mark.asyncio
async def test_query_agent_error_handling_real(query_agent, mock_query_engine):
    """Test error handling for empty and invalid queries."""
    # Test empty query
    result = await query_agent.process("")
    assert result["status"] == "error"
    assert "message" in result
    assert "Empty query" in result["message"]

    # Test invalid query
    mock_query_engine.execute_query.side_effect = Exception("Invalid query")
    result = await query_agent.process("Invalid query")
    assert result["status"] == "error"
    assert "message" in result
    assert "Error processing query" in result["message"]

@pytest.mark.asyncio
async def test_query_agent_with_knowledge(query_agent, mock_query_engine, mock_knowledge_store):
    """Test query agent with knowledge in graph."""
    # Mock responses for different queries
    mock_query_engine.execute_query.side_effect = [
        {
            "status": "success",
            "answer": "Answer 1",
            "confidence": 0.9,
            "explanation": "Explanation 1",
            "entities": [],
            "relationships": []
        },
        {
            "status": "success",
            "answer": "Answer 2",
            "confidence": 0.85,
            "explanation": "Explanation 2",
            "entities": [{"id": "1", "type": "test"}],
            "relationships": []
        }
    ]

    # Test first query
    result1 = await query_agent.process("Query 1")
    assert result1["status"] == "success"
    assert result1["data"]["answer"] == "Answer 1"
    assert result1["data"]["confidence"] == 0.9

    # Test second query
    result2 = await query_agent.process("Query 2")
    assert result2["status"] == "success"
    assert result2["data"]["answer"] == "Answer 2"
    assert result2["data"]["confidence"] == 0.85
    assert len(result2["data"]["entities"]) == 1

@pytest.mark.asyncio
async def test_query_agent_explanation_handling(query_agent, mock_query_engine):
    """Test that the query agent properly handles different explanation formats."""
    # Test with string explanation
    mock_query_engine.execute_query.return_value = {
        "status": "success",
        "answer": "Test answer",
        "confidence": 0.95,
        "explanation": "Simple explanation",
        "entities": [],
        "relationships": []
    }

    result = await query_agent.process("Test query")
    assert result["status"] == "success"
    assert "data" in result
    assert "explanation" in result["data"]
    assert result["data"]["explanation"] == "Simple explanation"

    # Test with dictionary explanation
    mock_query_engine.execute_query.return_value = {
        "status": "success",
        "answer": "Test answer",
        "confidence": 0.95,
        "explanation": {
            "reason": "Complex explanation",
            "details": ["Detail 1", "Detail 2"]
        },
        "entities": [],
        "relationships": []
    }

    result = await query_agent.process("Test query")
    assert result["status"] == "success"
    assert "data" in result
    assert "explanation" in result["data"]
    assert isinstance(result["data"]["explanation"], dict)
    assert "reason" in result["data"]["explanation"]
    assert "details" in result["data"]["explanation"]

@pytest.mark.asyncio
async def test_xai_metrics_handling(query_agent, mock_query_engine):
    """Test that the query agent properly handles XAI metrics."""
    mock_query_engine.execute_query.return_value = {
        "status": "success",
        "answer": "Test answer",
        "confidence": 0.95,
        "explanation": "Test explanation",
        "entities": [],
        "relationships": [],
        "xai_metrics": {
            "saliency": [0.1, 0.2, 0.3],
            "feature_importance": {"feature1": 0.8, "feature2": 0.6},
            "counterfactuals": ["alt1", "alt2"]
        }
    }

    result = await query_agent.process("Test query")
    assert result["status"] == "success"
    assert "data" in result
    assert "xai_metrics" in result["data"]
    assert "saliency" in result["data"]["xai_metrics"]
    assert "feature_importance" in result["data"]["xai_metrics"]
    assert "counterfactuals" in result["data"]["xai_metrics"] 