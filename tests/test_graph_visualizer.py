import pytest
import networkx as nx
import os
from cognisgraph.visualization.graph_visualizer import GraphVisualizer
from pathlib import Path

@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    G = nx.DiGraph()
    G.add_node("Paris", type="city", properties={"name": "Paris", "population": "2.1M"})
    G.add_node("France", type="country", properties={"name": "France", "population": "67M"})
    G.add_edge("Paris", "France", type="capital_of")
    return G

@pytest.fixture
def empty_graph():
    """Create an empty graph for testing."""
    return nx.DiGraph()

def test_graph_visualizer_initialization(sample_graph):
    """Test GraphVisualizer initialization."""
    visualizer = GraphVisualizer(sample_graph)
    assert visualizer.graph == sample_graph

def test_graph_visualizer_initialization_invalid():
    """Test GraphVisualizer initialization with invalid input."""
    with pytest.raises(TypeError):
        GraphVisualizer("invalid_graph")

def test_plot_networkx(sample_graph, tmp_path):
    """Test NetworkX plotting."""
    visualizer = GraphVisualizer(sample_graph)
    output_path = tmp_path / "test_networkx.png"
    visualizer.plot_networkx(output_path=str(output_path))
    assert output_path.exists()

def test_plot_networkx_empty(empty_graph):
    """Test NetworkX plotting with empty graph."""
    visualizer = GraphVisualizer(empty_graph)
    visualizer.plot_networkx()  # Should not raise an error

def test_plot_plotly(sample_graph, tmp_path):
    """Test Plotly plotting."""
    visualizer = GraphVisualizer(sample_graph)
    output_path = tmp_path / "test_plotly.html"
    fig = visualizer.plot_plotly(output_path=str(output_path))
    assert fig is not None
    assert output_path.exists()

def test_plot_plotly_empty(empty_graph):
    """Test Plotly plotting with empty graph."""
    visualizer = GraphVisualizer(empty_graph)
    fig = visualizer.plot_plotly()
    assert fig is not None

def test_plot_pyvis(sample_graph, tmp_path):
    """Test PyVis plotting."""
    visualizer = GraphVisualizer(sample_graph)
    output_path = tmp_path / "test_pyvis.html"
    visualizer.plot_pyvis(output_path=str(output_path))
    assert output_path.exists()

def test_plot_pyvis_empty(empty_graph, tmp_path):
    """Test PyVis plotting with empty graph."""
    visualizer = GraphVisualizer(empty_graph)
    output_path = tmp_path / "test_pyvis_empty.html"
    visualizer.plot_pyvis(output_path=str(output_path))
    assert output_path.exists()

def test_plot_graphviz(sample_graph, tmp_path):
    """Test Graphviz plotting."""
    visualizer = GraphVisualizer(sample_graph)
    output_path = tmp_path / "test_graphviz"
    visualizer.plot_graphviz(output_path=str(output_path))
    assert Path(f"{output_path}.png").exists()

def test_plot_graphviz_empty(empty_graph, tmp_path):
    """Test Graphviz plotting with empty graph."""
    visualizer = GraphVisualizer(empty_graph)
    output_path = tmp_path / "test_graphviz_empty"
    visualizer.plot_graphviz(output_path=str(output_path))
    assert Path(f"{output_path}.png").exists()

def test_plot_method(sample_graph, tmp_path):
    """Test the generic plot method with different visualization methods."""
    visualizer = GraphVisualizer(sample_graph)
    
    # Test plotly
    output_path = tmp_path / "test_plotly.html"
    result = visualizer.plot(method="plotly", output_path=str(output_path))
    assert result is not None
    assert output_path.exists()
    
    # Test networkx
    output_path = tmp_path / "test_networkx.png"
    visualizer.plot(method="networkx", output_path=str(output_path))
    assert output_path.exists()
    
    # Test pyvis
    output_path = tmp_path / "test_pyvis.html"
    visualizer.plot(method="pyvis", output_path=str(output_path))
    assert output_path.exists()
    
    # Test graphviz
    output_path = tmp_path / "test_graphviz"
    visualizer.plot(method="graphviz", output_path=str(output_path))
    assert Path(f"{output_path}.png").exists()

def test_plot_method_invalid(sample_graph):
    """Test the generic plot method with invalid visualization method."""
    visualizer = GraphVisualizer(sample_graph)
    with pytest.raises(ValueError):
        visualizer.plot(method="invalid_method") 