from typing import Optional, Dict, Any
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
import matplotlib.pyplot as plt
import graphviz
import logging

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """Enhanced visualization capabilities for CognisGraph."""
    
    def __init__(self, graph: nx.Graph):
        """Initializes the visualizer with the graph."""
        if not isinstance(graph, (nx.Graph, nx.DiGraph)):
            raise TypeError("graph must be a NetworkX Graph or DiGraph instance.")
        self.graph = graph
    
    def plot_networkx(self, layout: str = "spring", figsize: tuple = (10, 10),
                      node_color: str = 'lightblue', node_size: int = 500, **kwargs) -> None:
        """Plot the graph using NetworkX with matplotlib."""
        logger.info("Generating NetworkX plot...")
        if not self.graph or self.graph.number_of_nodes() == 0:
             logger.warning("Cannot plot empty graph with NetworkX.")
             return
        try:
             pos = getattr(nx, f"{layout}_layout")(self.graph)
             plt.figure(figsize=figsize)
             nx.draw(self.graph, pos, with_labels=True, node_color=node_color,
                     node_size=node_size, font_size=8, font_weight='bold')
             plt.title("Knowledge Graph Visualization")
             plt.show()
             logger.info("NetworkX plot generated.")
        except Exception as e:
             logger.error(f"Error generating NetworkX plot: {e}", exc_info=True)
             raise
    
    def plot_plotly(self, layout: str = "spring", node_size: int = 10, edge_width: float = 1.0, **kwargs) -> go.Figure:
        """Create an interactive Plotly visualization."""
        logger.info(f"Generating Plotly plot with layout: {layout}...")
        if not self.graph or self.graph.number_of_nodes() == 0:
             logger.warning("Cannot plot empty graph with Plotly.")
             # Return an empty figure or raise error?
             return go.Figure()
             
        # Create edge trace
        edge_trace = go.Scatter(
            x=[], y=[], line=dict(width=edge_width, color='#888'),
            hoverinfo='none', mode='lines')
        
        # Create node trace
        node_trace = go.Scatter(
            x=[], y=[], text=[], mode='markers+text',
            hoverinfo='text', marker=dict(
                showscale=True, colorscale='YlGnBu',
                size=node_size, colorbar=dict(
                    thickness=15, title='Node Connections',
                    xanchor='left'
                )
            )
        )
        
        # Add positions to traces
        try:
            layout_func = getattr(nx, f"{layout}_layout")
            pos = layout_func(self.graph)
        except AttributeError:
             logger.error(f"Invalid NetworkX layout specified: '{layout}'. Defaulting to spring_layout.")
             pos = nx.spring_layout(self.graph)
        except Exception as e:
             logger.error(f"Error calculating layout '{layout}': {e}. Defaulting to spring_layout.", exc_info=True)
             pos = nx.spring_layout(self.graph)
        
        # Node colors based on degree
        node_adjacencies = []
        node_text = []
        node_color_values = []
        
        for node, adjacencies in enumerate(self.graph.adjacency()):
             node_adjacencies.append(len(adjacencies[1]))
             node_info = f"{adjacencies[0]}<br># of connections: {len(adjacencies[1])}"
             # Add properties if they exist
             node_data = self.graph.nodes.get(adjacencies[0], {})
             node_info += f"<br>Type: {node_data.get('type', 'N/A')}"
             props = node_data.get('properties', {})
             for k, v in props.items():
                 node_info += f"<br>{k}: {v}"
             node_text.append(node_info)
             node_color_values.append(len(adjacencies[1])) # Color by degree

        # Populate node trace data
        for node in self.graph.nodes():
            x, y = pos[node]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)
        node_trace['text'] = node_text
        node_trace['marker']['color'] = node_color_values

        # Populate edge trace data
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title={
                    'text': '<br>Knowledge Graph Visualization (Plotly)',
                    'font': {'size': 16}
                },
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[ dict(
                    text="CognisGraph Interactive Visualization",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        logger.info("Plotly figure generated.")
        return fig
    
    def plot_pyvis(self, output_path: str = "knowledge_graph.html") -> None:
        """Create an interactive PyVis visualization."""
        logger.info(f"Generating PyVis plot to {output_path}...")
        if not self.graph or self.graph.number_of_nodes() == 0:
             logger.warning("Cannot plot empty graph with PyVis.")
             return
        try:
             net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
             
             # Add nodes and edges
             for node in self.graph.nodes():
                 net.add_node(node, title=node)
             
             for edge in self.graph.edges():
                 net.add_edge(edge[0], edge[1])
             
             # Save the visualization
             net.save_graph(output_path)
             logger.info("PyVis plot generated.")
        except Exception as e:
             logger.error(f"Error generating PyVis plot: {e}", exc_info=True)
             raise
    
    def plot_graphviz(self, output_path: str = "knowledge_graph") -> None:
        """Create a Graphviz visualization."""
        logger.info(f"Generating Graphviz plot to {output_path}.png...")
        if not self.graph or self.graph.number_of_nodes() == 0:
             logger.warning("Cannot plot empty graph with Graphviz.")
             return
        try:
             dot = graphviz.Digraph()
             
             # Add nodes and edges
             for node in self.graph.nodes():
                 dot.node(str(node))
             
             for edge in self.graph.edges():
                 dot.edge(str(edge[0]), str(edge[1]))
             
             # Save the visualization
             dot.render(output_path, format='png', cleanup=True)
             logger.info("Graphviz plot generated.")
        except ImportError:
             logger.error("Graphviz plot requires 'pygraphviz' package. Please install it.")
             raise
        except Exception as e:
             logger.error(f"Error generating Graphviz plot: {e}", exc_info=True)
             raise

# Example usage (if run directly)
if __name__ == "__main__":
    # Create a sample graph
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
    nx.set_node_attributes(G, {"A": {"type": "Start"}, "D": {"type": "End"}})
    
    # Initialize visualizer
    visualizer = GraphVisualizer(G)
    
    # Generate different plots
    try:
         visualizer.plot_networkx()
    except Exception as e:
         print(f"NetworkX plot failed: {e}")
         
    try:
         fig = visualizer.plot_plotly()
         fig.show() # Show Plotly figure in browser or IDE
         # fig.write_html("sample_plotly.html")
    except Exception as e:
         print(f"Plotly plot failed: {e}")
         
    try:
         visualizer.plot_pyvis("sample_pyvis.html")
    except Exception as e:
         print(f"PyVis plot failed: {e}")
         
    try:
         visualizer.plot_graphviz("sample_graphviz")
    except Exception as e:
         print(f"Graphviz plot failed: {e}") 