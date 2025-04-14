from core.state_graph import CognisGraphState, create_graph
from agents.base_agent import BaseAgent
from nlp.pdf_parser import PDFParser
from nlp.query_engine import QueryEngine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Demonstrate the Agent's functionality."""
    # Initialize components
    state_graph = create_graph()
    agent = BaseAgent()
    pdf_parser = PDFParser()
    query_engine = QueryEngine()
    
    # Example usage
    # Process a PDF
    pdf_state = CognisGraphState(
        messages=[],
        documents=[],
        input_type="pdf",
        content="path/to/sample.pdf"
    )
    pdf_result = state_graph.invoke(pdf_state.dict())
    
    # Process a query
    query_state = CognisGraphState(
        messages=[],
        documents=[],
        input_type="query",
        content="What is the main topic of the document?"
    )
    query_result = state_graph.invoke(query_state.dict())
    
    print("PDF Processing Result:", pdf_result)
    print("Query Result:", query_result)

if __name__ == "__main__":
    main() 