import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open, AsyncMock
import sys
from pathlib import Path
from cognisgraph import CognisGraph
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)

import asyncio

@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    from cognisgraph.core.knowledge_store import KnowledgeStore
    from cognisgraph.nlp.query_engine import QueryEngine
    
    class MockSessionState(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.__dict__ = self
    
    # Create a real KnowledgeStore instance
    knowledge_store = KnowledgeStore()
    
    # Mock its methods but keep the class instance
    knowledge_store.get_entities = Mock(return_value=[])
    knowledge_store.get_relationships = Mock(return_value=[])
    
    mock_cognisgraph = Mock()
    mock_query_agent = Mock()
    mock_ingestion_agent = Mock()
    query_engine = QueryEngine()
    
    state = MockSessionState({
        'knowledge_store': knowledge_store,
        'cognisgraph': mock_cognisgraph,
        'query_agent': mock_query_agent,
        'ingestion_agent': mock_ingestion_agent,
        'query_engine': query_engine
    })
    
    return state

@pytest.fixture
def mock_file_uploader():
    """Mock Streamlit file uploader."""
    with patch('streamlit.file_uploader') as mock:
        yield mock

@pytest.fixture
def mock_streamlit_config():
    """Mock Streamlit config."""
    config_content = """
[theme]
primaryColor = '#FF4B4B'
backgroundColor = '#FFFFFF'
secondaryBackgroundColor = '#F0F2F6'
textColor = '#262730'
font = 'sans serif'
"""
    with patch('builtins.open', mock_open(read_data=config_content)):
        yield

@pytest.fixture
def mock_viewer():
    with patch('cognisgraph.ui.components.KnowledgeGraphViewer') as mock:
        yield mock

@pytest.fixture
def mock_cognisgraph():
    """Create a mock CognisGraph instance."""
    mock = Mock(spec=CognisGraph)
    mock.add_knowledge = AsyncMock(return_value={
        "status": "success",
        "data": {
            "entities": [
                {"id": "doc1", "type": "document", "properties": {"content": "test content"}}
            ],
            "relationships": []
        }
    })
    mock.query = AsyncMock(return_value={
        "status": "success",
        "data": {
            "answer": "Test answer",
            "confidence": 0.9,
            "explanation": "Test explanation"
        }
    })
    mock.visualize = AsyncMock(return_value={
        "status": "success",
        "data": {
            "visualization": {"type": "graph", "data": {}}
        }
    })
    return mock

@pytest.fixture
def mock_file_upload():
    """Create a mock file upload with actual bytes data."""
    mock = Mock()
    mock.name = "test.pdf"
    mock.type = "application/pdf"
    mock.getbuffer.return_value = b"PDF file content"
    return mock

def test_document_processing(mock_session_state, mock_file_uploader, mock_streamlit_config, mock_viewer):
    """Test document processing in the Streamlit app."""
    # Setup
    mock_file = MagicMock()
    mock_file.name = "test.pdf"
    mock_file.type = "application/pdf"
    mock_file.getvalue.return_value = b"test content"
    mock_file_uploader.return_value = mock_file
    
    # Mock the CognisGraph methods
    mock_cognisgraph = Mock()
    mock_cognisgraph.process_pdf = AsyncMock(return_value={
        "status": "success",
        "data": {
            "entities": [],
            "relationships": [],
            "visualization": None
        }
    })
    
    # Mock other Streamlit components
    with patch('streamlit.session_state', mock_session_state), \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'), \
         patch('cognisgraph.ui.app.init_cognisgraph', new_callable=AsyncMock, return_value=mock_cognisgraph):
        
        # Import and run the app
        from cognisgraph.ui.app import main
        asyncio.run(main())
        
        # Verify
        mock_cognisgraph.process_pdf.assert_called_once()
        mock_success.assert_called_once_with("PDF processed successfully!")
        mock_error.assert_not_called()

def test_document_processing_error(mock_session_state, mock_file_uploader, mock_streamlit_config):
    """Test error handling during document processing."""
    # Setup
    mock_file = MagicMock()
    mock_file.name = "test.pdf"
    mock_file.type = "application/pdf"
    mock_file.getvalue.return_value = b"test content"
    mock_file_uploader.return_value = mock_file
    
    # Mock the CognisGraph to return an error
    mock_cognisgraph = Mock()
    mock_cognisgraph.process_pdf = AsyncMock(return_value={
        "status": "error",
        "error": "Test error"
    })
    
    # Mock other Streamlit components
    with patch('streamlit.session_state', mock_session_state), \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'), \
         patch('cognisgraph.ui.app.init_cognisgraph', new_callable=AsyncMock, return_value=mock_cognisgraph):
        
        # Import and run the app
        from cognisgraph.ui.app import main
        asyncio.run(main())
        
        # Verify
        mock_error.assert_called_once_with("Error processing PDF: Test error")
        assert not mock_success.called

def test_unsupported_file_type(mock_session_state, mock_file_uploader, mock_streamlit_config, mock_viewer):
    """Test handling of unsupported file types."""
    # Setup
    mock_file = MagicMock()
    mock_file.name = "test.xyz"
    mock_file.type = "application/xyz"
    mock_file.getvalue.return_value = b"test content"
    mock_file_uploader.return_value = mock_file

    # Create a mock cognisgraph object with process_pdf method
    mock_cognisgraph = Mock()
    mock_cognisgraph.process_pdf = AsyncMock(return_value={
        "status": "error",
        "error": "Unsupported file type: application/xyz"
    })

    # Mock other Streamlit components
    with patch('streamlit.session_state', mock_session_state), \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning'), \
         patch('os.path.exists', return_value=False), \
         patch('cognisgraph.ui.app.init_cognisgraph', new_callable=AsyncMock, return_value=mock_cognisgraph):

        # Import and run the app
        from cognisgraph.ui.app import main
        asyncio.run(main())

        # Verify
        mock_error.assert_called_once_with("Error processing PDF: Unsupported file type: application/xyz")
        mock_success.assert_not_called()

@pytest.mark.asyncio
async def test_document_processing(mock_cognisgraph, mock_file_upload):
    """Test successful document processing."""
    mock_cognisgraph.add_knowledge = AsyncMock(return_value={
        "status": "success",
        "data": {
            "entities": [],
            "relationships": []
        }
    })

    with patch("cognisgraph.ui.app.CognisGraph", return_value=mock_cognisgraph), \
         patch("os.path.exists", return_value=True):
        from cognisgraph.ui.app import process_pdf
        result = await process_pdf(mock_cognisgraph, "test.pdf")
        assert result["status"] == "success"
        assert "data" in result

@pytest.mark.asyncio
async def test_document_processing_error(mock_cognisgraph, mock_file_upload):
    """Test document processing with error."""
    with patch("cognisgraph.ui.app.CognisGraph", return_value=mock_cognisgraph), \
         patch("os.path.exists", return_value=False):
        from cognisgraph.ui.app import process_pdf
        result = await process_pdf(mock_cognisgraph, "test.pdf")
        assert result["status"] == "error"
        assert result["message"] == "File not found"

@pytest.mark.asyncio
async def test_unsupported_file_type(mock_cognisgraph):
    """Test handling of unsupported file types."""
    with patch("cognisgraph.ui.app.CognisGraph", return_value=mock_cognisgraph), \
         patch("os.path.exists", return_value=True):
        from cognisgraph.ui.app import process_pdf
        result = await process_pdf(mock_cognisgraph, "test.txt")
        assert result["status"] == "error"
        assert "unsupported file type" in result["message"].lower()

@pytest.mark.asyncio
async def test_query_processing(mock_cognisgraph):
    """Test query processing."""
    with patch("cognisgraph.ui.app.CognisGraph", return_value=mock_cognisgraph):
        from cognisgraph.ui.app import process_query
        
        result = await process_query(mock_cognisgraph, "test query")
        
        assert result["status"] == "success"
        assert "answer" in result["data"]
        assert result["data"]["answer"] == "Test answer"
        mock_cognisgraph.query.assert_called_once_with("test query")

@pytest.mark.asyncio
async def test_visualization_generation(mock_cognisgraph):
    """Test visualization generation."""
    with patch("cognisgraph.ui.app.CognisGraph", return_value=mock_cognisgraph):
        from cognisgraph.ui.app import generate_visualization
        
        result = await generate_visualization(mock_cognisgraph)
        
        assert result["status"] == "success"
        assert "visualization" in result["data"]
        assert result["data"]["visualization"]["type"] == "graph"
        mock_cognisgraph.visualize.assert_called_once() 