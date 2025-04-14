import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from cognisgraph.ui.components import KnowledgeGraphViewer
from cognisgraph.core.knowledge_store import Entity, Relationship

@pytest.fixture
def mock_session_state():
    """Create mock session state."""
    mock = MagicMock()
    mock.knowledge_store = MagicMock()
    mock.viewer = MagicMock()
    return mock

@pytest.fixture
def mock_viewer():
    """Create mock knowledge graph viewer."""
    viewer = MagicMock()
    viewer.create_figure = MagicMock()
    return viewer

@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock all Streamlit components."""
    with patch('streamlit.selectbox', return_value="spring"), \
         patch('streamlit.slider', side_effect=[10, 1.0]), \
         patch('streamlit.button', return_value=True), \
         patch('streamlit.columns', return_value=[MagicMock(), MagicMock()]), \
         patch('streamlit.plotly_chart'), \
         patch('streamlit.markdown'), \
         patch('streamlit.error'):
        yield

def test_visualization_empty_graph(mock_session_state, mock_viewer):
    """Test visualization with empty graph."""
    with patch('streamlit.session_state', mock_session_state):
        viewer = KnowledgeGraphViewer()
        viewer.create_figure = mock_viewer.create_figure
        
        viewer.display([], [])
        
        mock_viewer.create_figure.assert_called_once_with(
            [], [], "spring", 10, 1.0
        )

def test_visualization_entities_only(mock_session_state, mock_viewer):
    """Test visualization with only entities."""
    with patch('streamlit.session_state', mock_session_state):
        viewer = KnowledgeGraphViewer()
        viewer.create_figure = mock_viewer.create_figure
        
        entities = [
            Entity(id="1", type="Person", name="John", properties={"name": "John"}),
            Entity(id="2", type="Person", name="Jane", properties={"name": "Jane"})
        ]
        
        viewer.display(entities, [])
        
        mock_viewer.create_figure.assert_called_once_with(
            entities, [], "spring", 10, 1.0
        )

def test_visualization_with_relationships(mock_session_state, mock_viewer):
    """Test visualization with entities and relationships."""
    with patch('streamlit.session_state', mock_session_state):
        viewer = KnowledgeGraphViewer()
        viewer.create_figure = mock_viewer.create_figure
        
        entities = [
            Entity(id="1", type="Person", name="John", properties={"name": "John"}),
            Entity(id="2", type="Person", name="Jane", properties={"name": "Jane"})
        ]
        relationships = [
            Relationship(source="1", target="2", type="friend", properties={})
        ]
        
        viewer.display(entities, relationships)
        
        mock_viewer.create_figure.assert_called_once_with(
            entities, relationships, "spring", 10, 1.0
        )

def test_visualization_error_handling(mock_session_state, mock_viewer):
    """Test visualization error handling."""
    with patch('streamlit.session_state', mock_session_state):
        viewer = KnowledgeGraphViewer()
        viewer.create_figure = mock_viewer.create_figure
        mock_viewer.create_figure.side_effect = Exception("Test error")
        
        viewer.display([], [])
        
        st.error.assert_called_once()

def test_visualization_entity_name_handling(mock_session_state, mock_viewer):
    """Test visualization with entity names."""
    with patch('streamlit.session_state', mock_session_state):
        viewer = KnowledgeGraphViewer()
        viewer.create_figure = mock_viewer.create_figure
        
        entities = [
            Entity(id="1", type="Person", name="John", properties={"name": "John"}),
            Entity(id="2", type="Person", properties={})  # No name
        ]
        
        viewer.display(entities, [])
        
        mock_viewer.create_figure.assert_called_once_with(
            entities, [], "spring", 10, 1.0
        )