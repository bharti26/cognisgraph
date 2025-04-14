"""Example script for state graph visualization."""
from cognisgraph.core.state_graph import CognisGraphState, create_graph
import networkx as nx
import matplotlib.pyplot as plt

def visualize_state_graph():
    """Visualize the state graph structure."""
    # Create the graph
    graph = create_graph()
    
    # Create a NetworkX graph for visualization
    G = nx.DiGraph()
    
    # Add nodes
    for node in graph.nodes:
        G.add_node(node)
    
    # Add edges
    for source, target in graph.edges:
        G.add_edge(source, target)
    
    # Draw the graph
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=2000, font_size=10, font_weight='bold')
    plt.title("CognisGraph State Graph")
    plt.show()

def main():
    # Create a sample state
    state = CognisGraphState(
        messages=[],
        documents=[],
        input_type="pdf",
        content="path/to/sample.pdf"
    )
    
    # Visualize the state graph
    visualize_state_graph()
    
    # Print state information
    print("Sample State:")
    print(f"Input Type: {state.input_type}")
    print(f"Content: {state.content}")
    print(f"Number of Messages: {len(state.messages)}")
    print(f"Number of Documents: {len(state.documents)}")

if __name__ == "__main__":
    main() 