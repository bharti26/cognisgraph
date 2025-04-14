from core import CognisGraph

def main():
    # Initialize CognisGraph
    cg = CognisGraph()
    
    # Add some knowledge about Python
    python_knowledge = {
        "entity": "Python",
        "type": "Programming Language",
        "properties": {
            "created": 1991,
            "paradigm": ["object-oriented", "imperative", "functional"],
            "typing": "dynamic"
        },
        "relationships": [
            {
                "target": "Guido van Rossum",
                "type": "created_by",
                "properties": {"year": 1991}
            },
            {
                "target": "Python Software Foundation",
                "type": "maintained_by",
                "properties": {"since": 2001}
            }
        ]
    }
    
    # Add knowledge about Guido van Rossum
    guido_knowledge = {
        "entity": "Guido van Rossum",
        "type": "Person",
        "properties": {
            "born": 1956,
            "nationality": "Dutch",
            "occupation": "Programmer"
        }
    }
    
    # Add the knowledge to the graph
    cg.add_knowledge([python_knowledge, guido_knowledge])
    
    # Run a workflow
    print("\nRunning workflow with query about Python's creator:")
    result = cg.run_workflow(python_knowledge, "Who created Python?")
    print(f"Workflow result: {result}")
    
    # Query the graph
    print("\nQuerying about Python's creation:")
    query_result = cg.query("When was Python created?")
    print(f"Query result: {query_result}")
    
    # Visualize the graph using different methods
    print("\nGenerating visualizations...")
    
    # NetworkX visualization
    print("1. NetworkX visualization (static)")
    cg.visualize(method="networkx", layout="spring")
    
    # Plotly visualization
    print("2. Plotly visualization (interactive)")
    cg.visualize(method="plotly", output_path="python_graph_plotly.html")
    
    # PyVis visualization
    print("3. PyVis visualization (web-based)")
    cg.visualize(method="pyvis", output_path="python_graph_pyvis.html")
    
    # Graphviz visualization
    print("4. Graphviz visualization (high-quality)")
    cg.visualize(method="graphviz", output_path="python_graph")
    
    print("\nVisualizations have been generated. Check the output files:")
    print("- python_graph_plotly.html (Plotly interactive visualization)")
    print("- python_graph_pyvis.html (PyVis web-based visualization)")
    print("- python_graph.png (Graphviz visualization)")

if __name__ == "__main__":
    main() 