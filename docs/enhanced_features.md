# Enhanced Features

## State Management with LangGraph

The system now uses LangGraph for state management and workflow orchestration. This provides a more robust and flexible way to handle state transitions and workflow execution.

```python
from langgraph.graph import StateGraph
from core.state_graph import CognisGraphState, CognisGraphInput, CognisGraphOutput
from core.knowledge_store import KnowledgeStore
from nlp.query_engine import QueryEngine
from agents.orchestrator import Orchestrator
from agents import BaseAgent
from nlp.pdf_parser import PDFParser
from visualization.visualizer import Visualizer
from core.langgraph_workflow import CognisGraphWorkflow

# Initialize components
knowledge_store = KnowledgeStore()
query_engine = QueryEngine()
orchestrator = Orchestrator(knowledge_store, query_engine)

# Create state graph
state_graph = StateGraph(
    state_schema=CognisGraphState,
    input=CognisGraphInput,
    output=CognisGraphOutput
)

# Process input
input_data = {"type": "query", "content": "What are the main concepts?"}
result = state_graph.run(input_data)
```

## Query Processing

The query engine now supports more advanced query processing capabilities:

```python
# Execute a query
result = query_engine.execute_query("What are the main concepts?")
print(result)
```

## Knowledge Store Integration

The knowledge store provides a unified interface for storing and retrieving knowledge:

```python
# Add knowledge
knowledge_store.add_entity({"id": "test_entity", "type": "Person", "properties": {"name": "John Doe"}})

# Query knowledge
entities = knowledge_store.get_entities()
print(entities)
```

## Orchestration

The orchestrator manages the workflow between different components:

```python
# Process input through orchestrator
result = orchestrator.process("What are the main concepts?")
print(result)
```

## LangGraph Integration

CognisGraph now includes LangGraph integration for creating and managing complex knowledge graph workflows. The `CognisGraphWorkflow` class provides a framework for:

- Defining workflow states
- Creating custom nodes for knowledge operations
- Managing workflow execution
- Handling knowledge addition and query processing in a structured manner

### Example Usage

```python
from core import CognisGraph

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

## Agent System

CognisGraph implements a robust multi-agent system for processing knowledge and queries:

### Base Agent Architecture

The system is built on an abstract `Agent` class that defines core functionality:
- State management (IDLE, PROCESSING, VISUALIZING)
- Context handling
- Abstract processing interface

### Specialized Agents

1. **CognisGraphAgent**
   - Main orchestrator for knowledge operations
   - Handles both PDF processing and query execution
   - Manages state transitions and context
   - Integrates with KnowledgeStore and QueryEngine

### Example Usage

```python
from agents import BaseAgent
from nlp.pdf_parser import PDFParser
from nlp.query_engine import QueryEngine
from visualization.visualizer import Visualizer
from core.knowledge_store import KnowledgeStore

# Initialize components
pdf_parser = PDFParser()
query_engine = QueryEngine()
visualizer = Visualizer()
knowledge_store = KnowledgeStore()

# Create agent
agent = BaseAgent(
    pdf_parser=pdf_parser,
    query_engine=query_engine,
    knowledge_store=knowledge_store
)

# Process PDF
result = agent.process_pdf("document.pdf")
print(result)

# Process query
result = agent.process_query("What is the relationship between X and Y?")
print(result)
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
from core import CognisGraph

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
from core.langgraph_workflow import CognisGraphWorkflow

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