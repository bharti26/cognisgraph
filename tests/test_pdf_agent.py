import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from cognisgraph.agents.pdf_agent import PDFProcessingAgent
from cognisgraph.agents.query_agent import QueryAgent
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity
from cognisgraph.nlp.query_engine import QueryEngine
import tempfile
import json
from cognisgraph.nlp.pdf_parser import PDFParser

TEST_PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample.pdf")

@pytest.fixture
def knowledge_store():
    """Create a test knowledge store."""
    return KnowledgeStore()

@pytest.fixture
def mock_knowledge_store():
    """Create a mock knowledge store."""
    return Mock()

@pytest.fixture
def mock_entity_llm():
    """Mock LLM for entity extraction."""
    mock = Mock()
    def mock_completion(*args, **kwargs):
        response_dict = {
            "entities": [
                {
                    "id": "doc1",
                    "type": "Document",
                    "properties": {
                        "name": "test.pdf",
                        "content": "Test document content",
                        "title": "Test Document"
                    }
                },
                {
                    "id": "person1",
                    "type": "person",
                    "properties": {
                        "name": "John Doe",
                        "role": "author"
                    }
                }
            ],
            "relationships": [
                {
                    "source": "person1",
                    "target": "doc1",
                    "type": "authored",
                    "properties": {
                        "date": "2024-01-01"
                    }
                }
            ]
        }
        return json.dumps(response_dict)
    mock.invoke = Mock(side_effect=mock_completion)
    return mock

@pytest.fixture
def mock_pdf_parser():
    """Create a mock PDF parser."""
    return Mock(spec=PDFParser)

@pytest.fixture
def mock_embedding_llm():
    return Mock()

@pytest.fixture
def pdf_agent(knowledge_store):
    """Create a test PDF agent."""
    return PDFProcessingAgent(knowledge_store=knowledge_store)

@pytest.fixture
def query_engine(knowledge_store):
    return QueryEngine(knowledge_store)

@pytest.fixture
def query_agent(knowledge_store, query_engine):
    return QueryAgent(knowledge_store, query_engine)

@pytest.mark.asyncio
async def test_process_pdf_success(mock_pdf_parser, mock_knowledge_store):
    """Test successful PDF processing."""
    mock_pdf_parser.extract_text_from_pdf.return_value = "Test text"
    mock_pdf_parser.parse_pdf.return_value = {
        "text": "Test text",
        "entities": [{"id": "1", "type": "Person", "properties": {"name": "John"}}],
        "relationships": []
    }
    
    # Create agent with mocked parser
    agent = PDFProcessingAgent(mock_knowledge_store, None)
    agent.pdf_parser = mock_pdf_parser  # Replace the parser with our mock
    
    result = await agent.process(TEST_PDF_PATH)
    
    assert result["status"] == "success"
    assert "data" in result
    assert "entities" in result["data"]
    assert "relationships" in result["data"]
    assert len(result["data"]["entities"]) == 1
    assert len(result["data"]["relationships"]) == 0

@pytest.mark.asyncio
async def test_process_pdf_nonexistent_file(mock_pdf_parser, mock_knowledge_store):
    """Test handling of non-existent PDF file."""
    mock_pdf_parser.extract_text_from_pdf.side_effect = FileNotFoundError("File not found")
    mock_pdf_parser.parse_pdf.side_effect = FileNotFoundError("File not found")
    
    # Create agent with mocked parser
    agent = PDFProcessingAgent(mock_knowledge_store, None)
    agent.pdf_parser = mock_pdf_parser  # Replace the parser with our mock
    
    result = await agent.process("nonexistent.pdf")
    
    assert result["status"] == "error"
    assert "File not found" in result["message"]
    assert result["data"]["entities"] == []
    assert result["data"]["relationships"] == []

@pytest.mark.asyncio
async def test_process_pdf_invalid_file(mock_pdf_parser, mock_knowledge_store):
    """Test handling of invalid PDF file."""
    mock_pdf_parser.extract_text_from_pdf.side_effect = ValueError("Invalid PDF")
    mock_pdf_parser.parse_pdf.side_effect = ValueError("Invalid PDF")
    
    # Create agent with mocked parser
    agent = PDFProcessingAgent(mock_knowledge_store, None)
    agent.pdf_parser = mock_pdf_parser  # Replace the parser with our mock
    
    result = await agent.process(TEST_PDF_PATH)
    
    assert result["status"] == "error"
    assert "Invalid PDF" in result["message"]
    assert result["data"]["entities"] == []
    assert result["data"]["relationships"] == []

@pytest.mark.asyncio
async def test_process_pdf_empty_file(mock_pdf_parser, mock_knowledge_store):
    """Test handling of empty PDF file."""
    mock_pdf_parser.extract_text_from_pdf.return_value = ""
    mock_pdf_parser.parse_pdf.return_value = {
        "text": "",
        "entities": [],
        "relationships": []
    }
    
    # Create agent with mocked parser
    agent = PDFProcessingAgent(mock_knowledge_store, None)
    agent.pdf_parser = mock_pdf_parser  # Replace the parser with our mock
    
    result = await agent.process(TEST_PDF_PATH)
    
    assert result["status"] == "error"
    assert "No entities found in PDF" in result["message"]
    assert result["data"]["entities"] == []
    assert result["data"]["relationships"] == []

@pytest.mark.asyncio
async def test_process_pdf_extraction_error(mock_pdf_parser, mock_knowledge_store):
    """Test handling of entity extraction error."""
    mock_pdf_parser.extract_text_from_pdf.return_value = "Test text"
    mock_pdf_parser.parse_pdf.side_effect = Exception("Extraction error")
    
    # Create agent with mocked parser
    agent = PDFProcessingAgent(mock_knowledge_store, None)
    agent.pdf_parser = mock_pdf_parser  # Replace the parser with our mock
    
    result = await agent.process(TEST_PDF_PATH)
    
    assert result["status"] == "error"
    assert "Extraction error" in result["message"]
    assert result["data"]["entities"] == []
    assert result["data"]["relationships"] == []

@pytest.mark.asyncio
async def test_document_name_in_properties(mock_pdf_parser, mock_knowledge_store, mock_embedding_llm):
    """Test that document name is included in properties."""
    mock_pdf_parser.extract_text_from_pdf.return_value = "Test text"
    mock_pdf_parser.parse_pdf.return_value = {
        "text": "Test text",
        "entities": [{"id": "1", "type": "Person", "properties": {"name": "John", "document": os.path.basename(TEST_PDF_PATH)}}],
        "relationships": []
    }
    
    # Create agent with mocked parser
    agent = PDFProcessingAgent(mock_knowledge_store, None)
    agent.pdf_parser = mock_pdf_parser  # Replace the parser with our mock
    
    result = await agent.process(TEST_PDF_PATH)
    
    assert result["status"] == "success"
    assert "data" in result
    assert "entities" in result["data"]
    assert len(result["data"]["entities"]) == 1
    assert "document" in result["data"]["entities"][0]["properties"]
    assert result["data"]["entities"][0]["properties"]["document"] == os.path.basename(TEST_PDF_PATH)

def test_reset(pdf_agent, knowledge_store):
    """Test resetting the agent."""
    pdf_agent.reset()
    assert len(knowledge_store.get_graph().nodes) == 0
    assert len(knowledge_store.get_graph().edges) == 0