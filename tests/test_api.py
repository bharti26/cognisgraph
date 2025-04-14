import pytest
from fastapi.testclient import TestClient
from cognisgraph.api.endpoints import app
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship
from cognisgraph.agents.pdf_agent import PDFProcessingAgent
from unittest.mock import Mock, patch
import tempfile
import os

client = TestClient(app)

@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    return Mock()

@pytest.fixture
def knowledge_store():
    """Create a knowledge store for testing."""
    return KnowledgeStore()

@pytest.fixture
def pdf_agent(knowledge_store, mock_llm):
    """Create a PDF processing agent for testing."""
    return PDFProcessingAgent(knowledge_store, mock_llm)

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        # Write some dummy content
        temp_file.write(b"%PDF-1.4\n%EOF")
        return temp_file.name

def test_upload_pdf(sample_pdf, pdf_agent):
    """Test PDF upload endpoint."""
    # Mock the PDF processing agent
    with patch("cognisgraph.api.endpoints.pdf_agent") as mock_pdf_agent:
        # Configure the mock
        mock_pdf_agent.process.return_value = {
            "status": "success",
            "message": "PDF processed successfully",
            "entities": [],
            "relationships": []
        }
        
        # Create test client
        client = TestClient(app)
        
        # Open the sample PDF file
        with open(sample_pdf, "rb") as f:
            # Send POST request with file
            response = client.post(
                "/api/upload/pdf",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        # Check response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["message"] == "PDF processed successfully"
        
        # Verify mock was called correctly
        mock_pdf_agent.process.assert_called_once()
    os.unlink(sample_pdf)

def test_process_query():
    """Test query processing endpoint."""
    response = client.post("/api/query", json={"query": "What is the capital of France?"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_visualize_graph():
    """Test graph visualization endpoint."""
    response = client.get("/api/visualize?method=plotly")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["type"] == "plotly"

def test_get_entities():
    """Test get entities endpoint."""
    response = client.get("/api/entities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_relationships():
    """Test get relationships endpoint."""
    response = client.get("/api/relationships")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_add_entity():
    """Test add entity endpoint."""
    entity_data = {
        "id": "test_entity",
        "type": "test_type",
        "properties": {"name": "Test Entity"}
    }
    response = client.post("/api/entity", json=entity_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["entity"]["id"] == "test_entity"

def test_add_relationship():
    """Test add relationship endpoint."""
    # First add two entities
    entity1 = {
        "id": "source_entity",
        "type": "test_type",
        "properties": {"name": "Source Entity"}
    }
    entity2 = {
        "id": "target_entity",
        "type": "test_type",
        "properties": {"name": "Target Entity"}
    }
    client.post("/api/entity", json=entity1)
    client.post("/api/entity", json=entity2)
    
    # Then add the relationship
    relationship_data = {
        "source": "source_entity",
        "target": "target_entity",
        "type": "test_relationship",
        "properties": {"description": "Test relationship"}
    }
    response = client.post("/api/relationship", json=relationship_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["relationship"]["type"] == "test_relationship"

def test_invalid_visualization_method():
    """Test invalid visualization method."""
    response = client.get("/api/visualize?method=invalid")
    assert response.status_code == 400
    assert "Invalid visualization method" in response.json()["detail"]

def test_missing_required_fields():
    """Test missing required fields in entity creation."""
    entity_data = {
        "type": "test_type",  # Missing id
        "properties": {"name": "Test Entity"}
    }
    response = client.post("/api/entity", json=entity_data)
    assert response.status_code == 422  # Validation error 