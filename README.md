# CognisGraph

A powerful knowledge graph system with Explainable AI (XAI) features, built with Python.

## Features

- **Knowledge Store**: Efficient storage and retrieval of entities and relationships
- **Entity/Relationship Modeling**: Flexible data model for complex knowledge representation
- **Advanced Query Engine**: 
  - Natural language processing with LLaMA2 integration
  - Robust error handling and response validation
  - Parallel relationship processing
  - Intelligent response caching
- **Parsers**: Support for PDF and other document formats
- **Explainable AI (XAI)**:
  - Saliency analysis with graph centrality metrics
  - Feature importance with parallel processing
  - Counterfactual explanations
  - Rule extraction
  - Detailed confidence scoring
- **Multi-Agent Architecture**:
  - Query Agent with enhanced response handling
  - PDF Processing Agent with robust error management
  - Visualization Agent for graph rendering
  - Base Agent providing core functionality
- **Visualization**: Multiple layout options for graph visualization
- **Streamlit UI**: User-friendly interface for interaction

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Docker and Docker Compose (optional, for containerized deployment)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/bharti26/cognisgraph.git
cd cognisgraph
```

2. Choose one of the following installation methods:

#### Method 1: Local Installation (Recommended for Development)

1. Create and activate a virtual environment:
```bash
python3.11 -m venv cognisgraph_venv
source cognisgraph_venv/bin/activate  # On Windows: cognisgraph_venv\Scripts\activate
```

2. Install the package and its dependencies:
```bash
pip install -r requirements.txt
```

#### Method 2: Docker Installation (Recommended for Production)

1. Build and start the containers:
```bash
docker-compose up --build
```

This will start two services:
- API server on http://localhost:8000
- Streamlit UI on http://localhost:8501

2. To run in detached mode:
```bash
docker-compose up -d
```

3. To stop the services:
```bash
docker-compose down
```

4. To view logs:
```bash
docker-compose logs -f
```

## Usage

### Running the Streamlit App

```bash
streamlit run src/cognisgraph/ui/app.py
```

The app provides a user-friendly interface for:
- Uploading and processing PDF documents
- Querying the knowledge graph
- Visualizing entities and relationships
- Exploring explanations for query results

### Application Entry Points

The application can be run in different ways:

1. **Streamlit UI**: `src/cognisgraph/ui/app.py`
   - Full-featured web interface for interactive usage
   - Best for exploring and visualizing the knowledge graph

2. **Basic Test**: `examples/basic_test.py`
   - Simple script demonstrating core functionality
   - Good for quick testing of basic features

3. **Example Usage**: `examples/example_usage.py`
   - More comprehensive example showing various features
   - Useful for understanding the API and integration

### Using the Library Programmatically

```python
from core import CognisGraph

# Initialize the system
cognis = CognisGraph()

# Add knowledge
cognis.add_knowledge("Python is a programming language")
cognis.add_knowledge("Python is used for data science")

# Process a query
result = cognis.process_query("What is Python used for?")
print(result)
```

## Project Structure

```
cognisgraph/
├── src/
│   └── cognisgraph/
│       ├── core/           # Core functionality
│       ├── parsers/        # Document parsers
│       ├── xai/            # Explainable AI components
│       └── ui/             # Streamlit interface
├── tests/                  # Test suite
├── data/                   # Sample data
├── pyproject.toml          # Package configuration
├── requirements.txt        # Development requirements
└── README.md              # This file
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [NetworkX](https://networkx.org/) for graph operations
- [PyTorch](https://pytorch.org/) for deep learning capabilities
- [Streamlit](https://streamlit.io/) for the web interface
- [Sentence Transformers](https://www.sbert.net/) for semantic analysis

## 📞 Contact

For questions or support, please open an issue in the GitHub repository.

## Agent System Architecture

CognisGraph uses a multi-agent system architecture to handle different aspects of knowledge graph processing:

### Query Agent
- Natural language query processing
- Intelligent response transformation
- Robust error handling and validation
- Features:
  - Dual result/answer field support
  - Confidence scoring
  - Entity and relationship extraction
  - Explanation generation

### PDF Processing Agent
- Specialized in processing PDF documents
- Features:
  - Text extraction from PDF files
  - Entity and relationship extraction
  - Document metadata handling
  - Error recovery mechanisms

### Base Agent
- Provides core functionality for all agents
- Manages context and state
- Handles logging and error management
- Features:
  - Shared knowledge store access
  - Query engine integration
  - Consistent error handling patterns

### Visualization Agent
- Graph visualization and layout
- Interactive node/edge rendering
- Multiple layout algorithms
- Export capabilities

## Query Engine Features

The query engine provides sophisticated natural language processing:

### Response Processing
- Automatic response validation and cleaning
- Structured explanation generation
- Entity and relationship relevance scoring
- Confidence calculation based on graph metrics

### Performance Optimization
- LRU caching for formatted graph data
- Parallel relationship processing
- Chunked data handling for large graphs
- Response length optimization

### Graph Analysis
- Centrality metrics calculation
  - Degree centrality
  - Betweenness centrality
  - Closeness centrality
  - Eigenvector centrality with fallback
- Entity relevance scoring
- Relationship impact assessment 