import pytest
from unittest.mock import Mock, patch, AsyncMock
from cognisgraph.agents.orchestrator import OrchestratorAgent
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity

@pytest.fixture
def knowledge_store():
    return KnowledgeStore()

@pytest.fixture
def query_engine():
    mock_engine = Mock()
    mock_engine.llm = AsyncMock()
    mock_engine.llm.invoke.return_value = "Sample response"
    mock_engine.process_query.return_value = {
        "status": "success",
        "data": {
            "answer": "Test answer",
            "confidence": 0.9,
            "explanation": "Test explanation"
        }
    }
    return mock_engine

@pytest.fixture
def orchestrator(knowledge_store, query_engine):
    return OrchestratorAgent(knowledge_store, query_engine)

@pytest.mark.asyncio
async def test_process_pdf_success(orchestrator):
    # Mock successful PDF processing
    orchestrator.pdf_agent.process = AsyncMock(return_value={
        "status": "success",
        "data": {
            "entities": [
                {"id": "doc1", "type": "document", "properties": {"content": "test content", "page": 0}}
            ],
            "relationships": []
        }
    })
    
    # Mock knowledge store
    orchestrator.knowledge_store.get_entities = Mock(return_value=[
        {"id": "doc1", "type": "document", "properties": {"content": "test content", "page": 0}}
    ])
    orchestrator.knowledge_store.get_relationships = Mock(return_value=[])
    
    # Mock successful visualization
    orchestrator.visualization_agent.process = AsyncMock(return_value={
        "status": "success",
        "data": {
            "figure": {"type": "graph", "data": {}},
            "graph_info": {"num_nodes": 1, "num_edges": 0}
        }
    })
    
    result = await orchestrator.process({
        "type": "pdf",
        "content": "test.pdf"
    })
    
    assert result["status"] == "success"
    assert "data" in result
    assert "visualization" in result["data"]
    assert "pdf_path" in result["data"]
    assert result["data"]["pdf_path"] == "test.pdf"
    
    # Verify agents were called correctly
    orchestrator.pdf_agent.process.assert_called_once_with("test.pdf")
    orchestrator.knowledge_store.get_entities.assert_called_once()
    orchestrator.knowledge_store.get_relationships.assert_called_once()
    orchestrator.visualization_agent.process.assert_called_once_with({
        "entities": [{"id": "doc1", "type": "document", "properties": {"content": "test content", "page": 0}}],
        "relationships": []
    })

@pytest.mark.asyncio
async def test_process_pdf_failure(orchestrator):
    # Mock PDF processing failure
    error_msg = "File not found: nonexistent.pdf"
    orchestrator.pdf_agent.process = AsyncMock(return_value={
        "status": "error",
        "message": error_msg
    })
    
    result = await orchestrator.process({"type": "pdf", "content": "nonexistent.pdf"})
    
    assert result["status"] == "error"
    assert result["message"] == error_msg
    orchestrator.pdf_agent.process.assert_called_once_with("nonexistent.pdf")
    
@pytest.mark.asyncio
async def test_process_query(orchestrator):
    # Mock successful query processing
    query_result = {
        "status": "success",
        "data": {
            "result": "Query response"
        }
    }
    orchestrator.query_agent.process = AsyncMock(return_value=query_result)
    
    result = await orchestrator.process({"type": "query", "content": "What is the capital of France?"})
    
    assert result == query_result
    orchestrator.query_agent.process.assert_called_once_with("What is the capital of France?")

@pytest.mark.asyncio
async def test_process_visualization(orchestrator):
    # Mock successful visualization
    viz_data = {
        "entities": [Entity(id="1", type="test", properties={})],
        "relationships": []
    }
    viz_result = {
        "status": "success",
        "data": {
            "visualization": {"type": "graph", "data": {}}
        }
    }
    orchestrator.visualization_agent.process = AsyncMock(return_value=viz_result)
    
    result = await orchestrator.process({"type": "visualization", "content": viz_data})
    
    assert result == viz_result
    orchestrator.visualization_agent.process.assert_called_once_with({"type": "visualization", "content": viz_data})

def test_reset_all(orchestrator):
    # Mock agent reset methods
    orchestrator.pdf_agent.reset = Mock()
    orchestrator.query_agent.reset = Mock()
    orchestrator.visualization_agent.reset = Mock()
    
    orchestrator.reset_all()
    
    orchestrator.pdf_agent.reset.assert_called_once()
    orchestrator.query_agent.reset.assert_called_once()
    orchestrator.visualization_agent.reset.assert_called_once()

def test_get_agent_status(orchestrator):
    # Mock agent contexts
    orchestrator.pdf_agent.get_context = Mock(return_value={})
    orchestrator.query_agent.get_context = Mock(return_value={})
    orchestrator.visualization_agent.get_context = Mock(return_value={})
    
    status = orchestrator.get_agent_status()
    
    assert "pdf_agent" in status
    assert "query_agent" in status
    assert "visualization_agent" in status
    assert all(agent["status"] == "active" for agent in status.values())
    
    orchestrator.pdf_agent.get_context.assert_called_once()
    orchestrator.query_agent.get_context.assert_called_once()
    orchestrator.visualization_agent.get_context.assert_called_once() 