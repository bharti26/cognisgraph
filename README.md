# CognisGraph: Knowledge Graph Library with Explainable AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CognisGraph is a Python library designed for building, managing, and querying knowledge graphs. It integrates various components for data parsing, storage, querying, explainable AI (XAI), and visualization, making it easier to work with structured and unstructured knowledge.

## Features

*   **Knowledge Store:** Core component using NetworkX for graph storage and management (Entities, Relationships).
*   **Entity/Relationship Modeling:** Pydantic models for defining entities and relationships with properties.
*   **Query Engine:** Processes natural language queries using sentence embeddings (Sentence Transformers) to find relevant information.
*   **LLM-Powered Answers (Optional):** Generates natural language answers based on graph evidence using a local LLM (via Ollama integration - currently uses a placeholder).
*   **Parsers:** Includes a PDF parser (`PyPDF2`, NLTK) to extract entities and relationships from documents.
*   **Explainable AI (XAI):** Provides insights into query results and graph structure:
    *   Saliency Analysis (Centrality, Community Roles - placeholders)
    *   Feature Importance Analysis (placeholder)
    *   Counterfactual Explanations (placeholder)
    *   Rule Extraction (placeholder)
*   **Visualization:** Supports multiple backends (Matplotlib, Plotly, PyVis, Graphviz) for graph visualization.
*   **Streamlit UI:** An interactive web application for exploring the graph, querying, adding data, and viewing explanations.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/cognisgraph.git # Replace with your repo URL
    cd cognisgraph
    ```

2.  **Set up Virtual Environment & Install Dependencies using Makefile:**
    The easiest way is to use the provided Makefile:
    ```bash
    make install
    ```
    This command will:
    *   Create a Python virtual environment named `cognisgraph_venv_new` (if it doesn't exist).
    *   Install all required dependencies from `requirements.txt` into the virtual environment.
    *   Install the `cognisgraph` package itself in editable mode (`-e .`).

3.  **Download NLTK Data (Required for PDF Parser):**
    Run the following Python command (ideally within the activated venv) to download necessary NLTK models:
    ```python
    # Activate venv first: source cognisgraph_venv_new/bin/activate 
    python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng'); nltk.download('maxent_ne_chunker_tab')" 
    ```
    *(The PDF parser will also attempt to download these on first use if missing, but pre-downloading is recommended.)*

4.  **Install Ollama for Local LLM Answers (Optional):**
    To enable natural language answer generation using a local LLM:
    *   **Install Ollama:** Download and install from [https://ollama.com/](https://ollama.com/). Follow the instructions for your OS (macOS, Windows, Linux). Ensure the Ollama application/service is running in the background.
    *   **Download a Model:** Open your terminal and pull a recommended small model like Phi-3:
        ```bash
        ollama pull phi3
        ```
        *(Other models like `mistral` or `llama3` can be used if you have sufficient hardware, primarily GPU VRAM.)*
    *   **Verify Python Dependency:** Ensure the `requests` library is installed (it should be included in `requirements.txt`).

## Usage

### Running the Streamlit App

1.  **Activate the virtual environment:**
    ```bash
    source cognisgraph_venv_new/bin/activate
    ```
2.  **Run using Makefile:**
    ```bash
    make run
    ```
    This starts the Streamlit application (disabling the file watcher by default). Access it via the URL provided in the terminal (usually `http://localhost:8501`).

    *Note: If using the optional LLM integration, the first query might take longer as the local LLM loads.* 

### Using the Library Programmatically

```python
from cognisgraph import CognisGraph

# Initialize
cg = CognisGraph()

# Add Knowledge (Entity)
knowledge_item = {
    "entity": "New Concept",
    "type": "Idea",
    "properties": {"status": "initial", "created_by": "user"}
}
cg.add_knowledge(knowledge_item)

# Add Knowledge (Relationship to existing entities)
relationship_item = {
    "entity": "New Concept", # Source entity
    "relationships": [
        {
            "target": "Python", # Assumes 'Python' entity exists
            "type": "related_to",
            "properties": {"context": "example"}
        }
    ]
}
cg.add_knowledge(relationship_item)

# Process a Query
query = "What is New Concept related to?"
result = cg.process_query(query)
print(f"Query: {query}")
print(f"Answer: {result.answer}") 
# The UI uses result.evidence to format a better answer / feed an LLM

# Parse a PDF
# pdf_path = "path/to/your/document.pdf"
# cg.parse_pdf(pdf_path) # Adds extracted knowledge to the main store

# Get Explanations (Example)
# if result:
#     explanation = cg.explain_query_result(result)
#     print("\nExplanation:", explanation)

# Visualize 
# cg.visualize(method="plotly", output_path="graph.html")
```

## Testing

1.  **Activate the virtual environment:**
    ```bash
    source cognisgraph_venv_new/bin/activate
    ```
2.  **Run tests using Makefile:**
    ```bash
    make test 
    ```
    This executes the test suite using `pytest`.

## Project Structure

```
cognisgraph/
├── src/cognisgraph/             # Main source code
│   ├── core/                    # Core components (KnowledgeStore, QueryEngine)
│   ├── parsers/                 # Data parsers (PDFParser)
│   ├── visualization/           # Visualization logic
│   ├── xai/                     # Explainable AI components
│   ├── ui/                      # Streamlit UI application (app.py)
│   ├── utils/                   # Utility functions (logger, file watcher)
│   ├── __init__.py              # Package initialization
│   ├── cognisgraph.py           # Main facade class
│   ├── config.py                # Configuration (placeholder)
│   └── exceptions.py            # Custom exceptions
├── tests/                       # Pytest test files
├── examples/                    # Example usage scripts (basic_test.py)
├── .gitignore                   # Git ignore file
├── LICENSE                      # Project license (e.g., MIT)
├── Makefile                     # Makefile for common tasks (install, test, run, clean)
├── pyproject.toml               # Project metadata and build configuration
├── README.md                    # This file
└── requirements.txt             # Python dependencies
```

## Contributing

Contributions are welcome! Please follow standard fork-and-pull-request workflows. Ensure tests pass and consider adding new tests for new features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Streamlit Deployment

To deploy this app on Streamlit:

1. Fork this repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your forked repository
5. Set the following configuration:
   - Main file path: `streamlit_app.py`
   - Python version: 3.8 or higher
   - Requirements file: `requirements_streamlit.txt`

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements_streamlit.txt
   ```
4. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```

## Project Structure

- `src/cognisgraph/`: Main package code
- `src/cognisgraph/core/`: Core functionality
- `src/cognisgraph/ui/`: Streamlit UI components
- `src/cognisgraph/xai/`: Explainable AI features
- `tests/`: Test files
- `examples/`: Example usage scripts

## License

MIT License 