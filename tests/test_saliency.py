"""Integration tests for saliency analysis."""

import pytest
import networkx as nx
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship
from cognisgraph.xai.saliency import SaliencyAnalyzer

@pytest.fixture
def knowledge_store():
    """Create a knowledge store with test data."""
    store = KnowledgeStore()
    
    # Add test entities with more properties for better analysis
    python = Entity(
        id="python", 
        type="Language", 
        properties={
            "name": "Python", 
            "popularity": "high",
            "year_created": 1991,
            "paradigm": ["procedural", "object-oriented", "functional"]
        }
    )
    streamlit = Entity(
        id="streamlit", 
        type="Framework", 
        properties={
            "name": "Streamlit", 
            "language": "Python",
            "year_created": 2019,
            "category": "web"
        }
    )
    pandas = Entity(
        id="pandas", 
        type="Library", 
        properties={
            "name": "Pandas", 
            "language": "Python",
            "year_created": 2008,
            "category": "data"
        }
    )
    numpy = Entity(
        id="numpy",
        type="Library",
        properties={
            "name": "NumPy",
            "language": "Python",
            "year_created": 2006,
            "category": "data"
        }
    )
    
    # Add entities
    store.add_entity(python)
    store.add_entity(streamlit)
    store.add_entity(pandas)
    store.add_entity(numpy)
    
    # Add relationships with more properties
    store.add_relationship(Relationship(
        source="streamlit",
        target="python",
        type="built_with",
        properties={
            "version": "3.8+",
            "dependency": "direct",
            "year_added": 2019
        }
    ))
    
    store.add_relationship(Relationship(
        source="pandas",
        target="python",
        type="built_with",
        properties={
            "version": "3.7+",
            "dependency": "direct",
            "year_added": 2008
        }
    ))
    
    store.add_relationship(Relationship(
        source="pandas",
        target="numpy",
        type="depends_on",
        properties={
            "version": "1.20+",
            "dependency": "direct",
            "year_added": 2008
        }
    ))
    
    store.add_relationship(Relationship(
        source="numpy",
        target="python",
        type="built_with",
        properties={
            "version": "3.7+",
            "dependency": "direct",
            "year_added": 2006
        }
    ))
    
    return store

@pytest.fixture
def empty_knowledge_store():
    """Create an empty knowledge store for testing edge cases."""
    return KnowledgeStore()

@pytest.fixture
def saliency_analyzer(knowledge_store):
    """Create a saliency analyzer with the test knowledge store."""
    return SaliencyAnalyzer(knowledge_store)

@pytest.fixture
def empty_saliency_analyzer(empty_knowledge_store):
    """Create a saliency analyzer with an empty knowledge store."""
    return SaliencyAnalyzer(empty_knowledge_store)

def test_saliency_analyzer_initialization(knowledge_store):
    """Test that the saliency analyzer initializes correctly."""
    analyzer = SaliencyAnalyzer(knowledge_store)
    assert analyzer.knowledge_store == knowledge_store
    assert isinstance(analyzer.graph, nx.DiGraph)
    assert len(analyzer.graph.nodes()) > 0
    assert len(analyzer.graph.edges()) > 0

def test_saliency_analyzer_with_empty_store(empty_knowledge_store):
    """Test that the saliency analyzer handles empty knowledge store correctly."""
    analyzer = SaliencyAnalyzer(empty_knowledge_store)
    assert analyzer.knowledge_store == empty_knowledge_store
    assert isinstance(analyzer.graph, nx.DiGraph)
    assert len(analyzer.graph.nodes()) == 0
    assert len(analyzer.graph.edges()) == 0

def test_analyze_with_valid_nodes(saliency_analyzer):
    """Test saliency analysis with valid nodes."""
    result = saliency_analyzer.analyze(target_nodes=["python", "pandas"])
    
    assert "centrality_scores" in result
    assert "path_importance" in result
    assert "community_role" in result
    
    # Check centrality scores
    centrality_scores = result["centrality_scores"]
    assert "python" in centrality_scores
    assert "pandas" in centrality_scores
    
    # Verify all centrality measures are present
    for node in ["python", "pandas"]:
        scores = centrality_scores[node]
        assert "degree_centrality" in scores
        assert "betweenness_centrality" in scores
        assert "closeness_centrality" in scores
        assert "eigenvector_centrality" in scores
        
        # Verify scores are between 0 and 1
        for score in scores.values():
            assert 0 <= score <= 1

def test_analyze_with_invalid_nodes(saliency_analyzer):
    """Test saliency analysis with invalid nodes."""
    result = saliency_analyzer.analyze(target_nodes=["nonexistent1", "nonexistent2"])
    assert result == saliency_analyzer._default_analysis()

def test_analyze_with_mixed_nodes(saliency_analyzer):
    """Test saliency analysis with a mix of valid and invalid nodes."""
    result = saliency_analyzer.analyze(target_nodes=["python", "nonexistent"])
    
    assert "centrality_scores" in result
    assert "python" in result["centrality_scores"]
    assert "nonexistent" not in result["centrality_scores"]

def test_analyze_with_empty_graph(empty_saliency_analyzer):
    """Test saliency analysis with an empty graph."""
    result = empty_saliency_analyzer.analyze()
    assert result == empty_saliency_analyzer._default_analysis()

def test_analyze_path_importance(saliency_analyzer):
    """Test path importance analysis."""
    result = saliency_analyzer.analyze(target_nodes=["python", "pandas", "numpy"])
    
    assert "path_importance" in result
    path_importance = result["path_importance"]
    
    # Check for expected paths
    assert "python-pandas" in path_importance
    assert "python-numpy" in path_importance
    assert "pandas-numpy" in path_importance
    
    # Verify path importance structure
    for path_data in path_importance.values():
        assert "paths" in path_data
        assert "importance" in path_data
        assert isinstance(path_data["importance"], float)
        assert 0 <= path_data["importance"] <= 1

def test_analyze_community_role(saliency_analyzer):
    """Test community role analysis."""
    result = saliency_analyzer.analyze(target_nodes=["python", "pandas", "numpy"])
    
    assert "community_role" in result
    community_role = result["community_role"]
    
    # Check community roles for each node
    for node in ["python", "pandas", "numpy"]:
        assert node in community_role
        role_data = community_role[node]
        assert "community_id" in role_data
        assert "role" in role_data
        assert "community_size" in role_data
        assert role_data["role"] in ["Hub", "Connector", "Member", "Peripheral", "Isolated"]

def test_calculate_centrality(saliency_analyzer):
    """Test individual centrality calculation."""
    scores = saliency_analyzer.calculate_centrality("python")
    
    assert "degree_centrality" in scores
    assert "betweenness_centrality" in scores
    assert "closeness_centrality" in scores
    assert "eigenvector_centrality" in scores
    
    # Verify scores are between 0 and 1
    for score in scores.values():
        assert 0 <= score <= 1

def test_calculate_centrality_invalid_node(saliency_analyzer):
    """Test centrality calculation for invalid node."""
    scores = saliency_analyzer.calculate_centrality("nonexistent")
    assert all(score == 0.0 for score in scores.values())

def test_clear_cache(saliency_analyzer):
    """Test cache clearing functionality."""
    # First run to populate cache
    saliency_analyzer.analyze(target_nodes=["python"])
    assert saliency_analyzer._centrality_cache
    
    # Clear cache
    saliency_analyzer.clear_cache()
    assert not saliency_analyzer._centrality_cache

def test_saliency_analyzer_with_invalid_graph():
    """Test that SaliencyAnalyzer raises TypeError when initialized with invalid graph."""
    # Create a mock knowledge store with a dictionary instead of a NetworkX graph
    class MockKnowledgeStore:
        def __init__(self):
            self.graph = {}  # Invalid graph type

    with pytest.raises(TypeError) as exc_info:
        SaliencyAnalyzer(MockKnowledgeStore())
    assert "must be an instance of KnowledgeStore" in str(exc_info.value) 