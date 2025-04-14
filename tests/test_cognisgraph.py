"""Tests for the CognisGraph application."""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
import networkx as nx
from cognisgraph.app import CognisGraph
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship
from cognisgraph.nlp.query_engine import QueryEngine
from cognisgraph.agents.orchestrator import OrchestratorAgent
from cognisgraph.utils.logger import CognisGraphLogger

@pytest_asyncio.fixture
def mock_knowledge_store():
    """Create a mock KnowledgeStore."""
    store = Mock()
    store.get_entities.return_value = []
    store.get_relationships.return_value = []
    store.get_entity.return_value = None
    return store

@pytest_asyncio.fixture
def mock_query_engine():
    """Create a mock QueryEngine."""
    engine = Mock()
    engine.process_query.return_value = {
        "answer": "Test answer",
        "confidence": 0.8,
        "explanation": "Test explanation",
        "relevant_entities": [],
        "relevant_relationships": []
    }
    return engine

@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    mock = Mock()
    mock.process = AsyncMock(return_value={
        "status": "success",
        "data": {
            "entities": [],
            "relationships": [],
            "visualization": None
        }
    })
    return mock

@pytest.fixture
def mock_config():
    config = {
        "log_level": "INFO",
        "visualization": {
            "default_method": "plotly"
        }
    }
    return config

@pytest.mark.asyncio
async def test_initialization(mock_knowledge_store, mock_query_engine, mock_orchestrator, mock_config):
    """Test CognisGraph initialization."""
    with patch("cognisgraph.app.KnowledgeStore", return_value=mock_knowledge_store), \
         patch("cognisgraph.app.QueryEngine", return_value=mock_query_engine), \
         patch("cognisgraph.app.OrchestratorAgent", return_value=mock_orchestrator):
        app = CognisGraph(mock_config)
        assert app.knowledge_store == mock_knowledge_store
        assert app.query_engine == mock_query_engine
        assert app.orchestrator == mock_orchestrator

@pytest.mark.asyncio
async def test_add_knowledge(cognisgraph, mock_orchestrator):
    result = await cognisgraph.add_knowledge("test.pdf")
    assert result["status"] == "success"
    mock_orchestrator.process.assert_called_once_with({
        "type": "pdf",
        "content": "test.pdf"
    })

@pytest.mark.asyncio
async def test_query(cognisgraph, mock_orchestrator):
    query = "Find all people who work at TechCorp"
    result = await cognisgraph.query(query)
    assert result["status"] == "success"
    mock_orchestrator.process.assert_called_once_with({
        "type": "query",
        "content": query
    })

@pytest.mark.asyncio
async def test_visualize(cognisgraph, mock_orchestrator):
    result = await cognisgraph.visualize(method="plotly")
    assert result["status"] == "success"
    assert "result" in result
    mock_orchestrator.process.assert_called_once_with({
        "type": "visualization",
        "method": "plotly",
        "output_path": None
    })

@pytest.mark.asyncio
async def test_get_entities(cognisgraph, mock_knowledge_store):
    result = await cognisgraph.get_entities()
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(e, Entity) for e in result)
    mock_knowledge_store.get_entities.assert_called_once()

@pytest.mark.asyncio
async def test_get_relationships(cognisgraph, mock_knowledge_store):
    result = await cognisgraph.get_relationships()
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Relationship)
    assert result[0].source == "1"
    assert result[0].type == "WORKS_FOR"
    mock_knowledge_store.get_relationships.assert_called_once()

@pytest.mark.asyncio
async def test_get_entity(cognisgraph, mock_knowledge_store):
    entity_id = "1"
    result = await cognisgraph.get_entity(entity_id)
    assert isinstance(result, Entity)
    assert result.id == "1"
    assert result.type == "Person"
    mock_knowledge_store.get_entity.assert_called_once_with(entity_id)

@pytest.mark.asyncio
async def test_run_workflow(mock_knowledge_store, mock_query_engine, mock_orchestrator, mock_config):
    """Test running a complete workflow."""
    with patch("cognisgraph.app.KnowledgeStore", return_value=mock_knowledge_store), \
         patch("cognisgraph.app.QueryEngine", return_value=mock_query_engine), \
         patch("cognisgraph.app.OrchestratorAgent", return_value=mock_orchestrator):
        app = CognisGraph(mock_config)
        result = await app.run_workflow("test.pdf", "test query")
        assert result["status"] == "success"
        assert mock_orchestrator.process.call_count == 2
        mock_orchestrator.process.assert_any_call({
            "type": "pdf",
            "content": "test.pdf"
        })
        mock_orchestrator.process.assert_any_call({
            "type": "query",
            "content": "test query"
        })

@pytest.fixture
def mock_knowledge_store():
    store = Mock(spec=KnowledgeStore)
    store.graph = nx.DiGraph()
    
    # Add test data to the graph
    store.graph.add_node("1", type="Person", properties={"name": "John"})
    store.graph.add_node("2", type="Company", properties={"name": "TechCorp"})
    store.graph.add_edge("1", "2", type="WORKS_FOR", properties={})
    
    # Set up mock methods
    store.get_entity = Mock(return_value=Entity(id="1", type="Person", properties={"name": "John"}))
    store.get_entities = Mock(return_value=[
        Entity(id="1", type="Person", properties={"name": "John"}),
        Entity(id="2", type="Company", properties={"name": "TechCorp"})
    ])
    store.get_relationships = Mock(return_value=[
        Relationship(source="1", target="2", type="WORKS_FOR", properties={})
    ])
    store.get_graph = Mock(return_value=store.graph)
    return store

@pytest.fixture
def mock_query_engine():
    engine = Mock(spec=QueryEngine)
    engine.execute_query.return_value = {
        "status": "success",
        "answer": "Test answer",
        "confidence": 0.95,
        "explanation": "Test explanation",
        "entities": [],
        "relationships": []
    }
    return engine

@pytest.fixture
def mock_orchestrator():
    orchestrator = Mock(spec=OrchestratorAgent)
    async def mock_process(*args, **kwargs):
        return {
            "status": "success",
            "result": {
                "answer": "Test answer",
                "confidence": 0.95,
                "explanation": "Test explanation",
                "entities": [],
                "relationships": []
            }
        }
    orchestrator.process = Mock(side_effect=mock_process)
    return orchestrator

@pytest.fixture
def cognisgraph(mock_knowledge_store, mock_query_engine, mock_orchestrator, mock_config):
    app = CognisGraph()
    app.config = mock_config
    app.knowledge_store = mock_knowledge_store
    app.query_engine = mock_query_engine
    app.orchestrator = mock_orchestrator
    return app

@pytest.mark.asyncio
async def test_cognisgraph_initialization_with_config():
    config = {
        "log_level": "INFO",
        "log_file": "test.log"
    }
    store = KnowledgeStore()
    store.graph = nx.DiGraph()
    with patch('cognisgraph.core.knowledge_store.KnowledgeStore', return_value=store), \
         patch('cognisgraph.nlp.query_engine.QueryEngine'), \
         patch('cognisgraph.agents.orchestrator.OrchestratorAgent'):
        app = CognisGraph(config=config)
        assert app.logger is not None
        assert isinstance(app.logger, CognisGraphLogger)

@pytest.mark.asyncio
async def test_add_knowledge(cognisgraph, mock_orchestrator):
    result = await cognisgraph.add_knowledge("test.pdf")
    assert result["status"] == "success"
    mock_orchestrator.process.assert_called_once_with({
        "type": "pdf",
        "content": "test.pdf"
    })

@pytest.mark.asyncio
async def test_query(cognisgraph, mock_orchestrator):
    query = "Find all people who work at TechCorp"
    result = await cognisgraph.query(query)
    assert result["status"] == "success"
    mock_orchestrator.process.assert_called_once_with({
        "type": "query",
        "content": query
    })

@pytest.mark.asyncio
async def test_visualize(cognisgraph, mock_orchestrator):
    result = await cognisgraph.visualize(method="plotly")
    assert result["status"] == "success"
    assert "result" in result
    mock_orchestrator.process.assert_called_once_with({
        "type": "visualization",
        "method": "plotly",
        "output_path": None
    })

def test_get_entities(cognisgraph, mock_knowledge_store):
    result = cognisgraph.get_entities()
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(e, Entity) for e in result)
    mock_knowledge_store.get_entities.assert_called_once()

def test_get_relationships(cognisgraph, mock_knowledge_store):
    result = cognisgraph.get_relationships()
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Relationship)
    assert result[0].source == "1"
    assert result[0].type == "WORKS_FOR"
    mock_knowledge_store.get_relationships.assert_called_once()

def test_get_entity(cognisgraph, mock_knowledge_store):
    entity_id = "1"
    result = cognisgraph.get_entity(entity_id)
    assert isinstance(result, Entity)
    assert result.id == "1"
    assert result.type == "Person"
    mock_knowledge_store.get_entity.assert_called_once_with(entity_id) 