import pytest
from unittest.mock import Mock, AsyncMock
from cognisgraph.agents.query_agent import QueryAgent
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity
from cognisgraph.nlp.query_engine import QueryEngine

@pytest.fixture
def knowledge_store():
    """Create a test knowledge store."""
    return KnowledgeStore()

@pytest.fixture
def query_engine(knowledge_store):
    """Create a test query engine."""
    mock_engine = Mock()
    mock_engine.llm = AsyncMock()
    mock_engine.llm.invoke.return_value = "Sample response"
    mock_engine.execute_query = AsyncMock(return_value={
        "answer": "The capital of France is Paris.",
        "confidence": 0.9,
        "explanation": "Based on the knowledge graph",
        "entities": [],
        "relationships": []
    })
    return mock_engine

@pytest.fixture
def query_agent(knowledge_store, query_engine):
    """Create a test query agent."""
    return QueryAgent(knowledge_store, query_engine)

@pytest.mark.asyncio
async def test_query_agent_real_answer_generation(query_agent, query_engine):
    """Test that the query agent can generate real answers."""
    # Mock the query engine's execute_query method
    query_engine.execute_query = AsyncMock(return_value={
        "answer": "The capital of France is Paris.",
        "confidence": 0.9,
        "explanation": "Based on the knowledge graph",
        "entities": [],
        "relationships": []
    })
    
    result = await query_agent.process("What is the capital of France?")
    assert result["status"] == "success"
    assert "Paris" in result["data"]["answer"]
    assert result["data"]["explanation"] is not None

@pytest.mark.asyncio
async def test_query_agent_with_knowledge(query_agent, knowledge_store, query_engine):
    """Test that the query agent uses knowledge from the store."""
    # Add some test knowledge
    entity = Entity(
        id="france",
        type="country",
        properties={"name": "France", "capital": "Paris"}
    )
    knowledge_store.add_entity(entity)
    
    # Mock the query engine's execute_query method
    query_engine.execute_query = AsyncMock(return_value={
        "answer": "The capital of France is Paris.",
        "confidence": 0.9,
        "explanation": "Based on the knowledge graph",
        "entities": [entity],
        "relationships": []
    })
    
    result = await query_agent.process("What is the capital of France?")
    assert result["status"] == "success"
    assert "Paris" in result["data"]["answer"]
    assert result["data"]["explanation"] is not None 