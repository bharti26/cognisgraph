# Enhanced CognisGraph Features

## LangGraph Integration

CognisGraph now includes LangGraph integration for creating and managing complex knowledge graph workflows. The `CognisGraphWorkflow` class provides a framework for:

- Defining workflow states
- Creating custom nodes for knowledge operations
- Managing workflow execution
- Handling knowledge addition and query processing in a structured manner

### Example Usage

```python
from cognisgraph import CognisGraph

# Initialize CognisGraph
cg = CognisGraph()

# Define knowledge and query
knowledge = {
    "entity": "Python",
    "type": "Programming Language",
    "properties": {"created": 1991},
    "relationships": [
        {
            "target": "Guido van Rossum",
            "type": "created_by",
            "properties": {"year": 1991}
        }
    ]
}

query = "Who created Python?"

# Run the workflow
result = cg.run_workflow(knowledge, query)
```

## Enhanced Visualization

CognisGraph now supports multiple visualization methods through the `GraphVisualizer` class:

### Available Visualization Methods

1. **NetworkX (Matplotlib)**
   - Static visualization
   - Good for quick inspection
   - Customizable layout and styling

2. **Plotly**
   - Interactive visualization
   - Hover information
   - Zoom and pan capabilities
   - Export to HTML

3. **PyVis**
   - Interactive web-based visualization
   - Node dragging
   - Physics-based layout
   - Export to HTML

4. **Graphviz**
   - High-quality static visualization
   - Professional-looking layouts
   - Export to various formats (PNG, PDF, SVG)

### Example Usage

```python
from cognisgraph import CognisGraph

# Initialize CognisGraph
cg = CognisGraph()

# Add some knowledge
cg.add_knowledge({
    "entity": "Python",
    "type": "Programming Language",
    "properties": {"created": 1991}
})

# Visualize using different methods
cg.visualize(method="networkx")  # Static matplotlib plot
cg.visualize(method="plotly")    # Interactive plotly visualization
cg.visualize(method="pyvis", output_path="graph.html")  # Interactive web visualization
cg.visualize(method="graphviz", output_path="graph")    # Graphviz visualization
```

## Best Practices

1. **Workflow Design**
   - Keep workflow states simple and focused
   - Use clear node names and edge definitions
   - Document custom nodes and their purposes

2. **Visualization**
   - Choose the visualization method based on your needs:
     - Use NetworkX for quick debugging
     - Use Plotly for interactive exploration
     - Use PyVis for web-based sharing
     - Use Graphviz for publication-quality graphics

3. **Performance**
   - For large graphs, consider using PyVis or Graphviz
   - Use appropriate layout algorithms for your graph size
   - Cache visualization results when possible

## Advanced Features

### Custom Workflow Nodes

You can extend the `CognisGraphWorkflow` class to add custom nodes:

```python
from cognisgraph.core.langgraph_workflow import CognisGraphWorkflow

class CustomWorkflow(CognisGraphWorkflow):
    def _create_workflow(self):
        workflow = super()._create_workflow()
        
        # Add custom node
        def custom_processing(state, data):
            # Custom processing logic
            return state
        
        workflow.add_node("custom_processing", custom_processing)
        workflow.add_edge("process_query", "custom_processing")
        
        return workflow
```

### Custom Visualization Styles

You can customize the visualization appearance:

```python
# Customize Plotly visualization
cg.visualize(
    method="plotly",
    layout="circular",
    node_size=20,
    edge_width=2
)

# Customize NetworkX visualization
cg.visualize(
    method="networkx",
    layout="kamada_kawai",
    node_color="red",
    node_size=1000
)
```

## Troubleshooting

1. **Workflow Issues**
   - Check workflow state consistency
   - Verify node and edge definitions
   - Ensure proper error handling in custom nodes

2. **Visualization Issues**
   - For large graphs, try different layout algorithms
   - Adjust node and edge sizes for better visibility
   - Use appropriate output formats for your needs 