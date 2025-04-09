import pytest
import os
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.core.query_engine import QueryEngine
from cognisgraph.parsers.pdf_parser import PDFParser

@pytest.fixture
def sample_pdf_path():
    """Return the path to the sample PDF file."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample.pdf")

def test_pdf_parsing(sample_pdf_path):
    """Test PDF parsing and integration with knowledge store."""
    # Initialize components
    store = KnowledgeStore()
    query_engine = QueryEngine(store)
    parser = PDFParser()
    
    try:
        # Parse the PDF
        print("\nParsing PDF...")
        parsed_store = parser.parse_pdf(sample_pdf_path)
        
        # Print extraction statistics
        print(f"\nExtracted {len(parsed_store.entity_index)} entities")
        print(f"Extracted {len(parsed_store.relationship_index)} relationships")
        
        # Print sample entities
        print("\nSample Entities:")
        for entity in list(parsed_store.entity_index.values())[:5]:
            print(f"- {entity.type}: {entity.properties['text']}")
        
        # Print sample relationships
        print("\nSample Relationships:")
        for rel in list(parsed_store.relationship_index.values())[:5]:
            print(f"- {rel.type}: {rel.source} → {rel.target}")
        
        # Add to main knowledge store
        for entity in parsed_store.entity_index.values():
            store.add_entity(entity)
        
        for relationship in parsed_store.relationship_index.values():
            store.add_relationship(relationship)
        
        # Try some queries
        print("\nTesting queries...")
        test_queries = [
            "Who works at TechCorp?",
            "What is Project Phoenix?",
            "What is the relationship between John and Alice?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            result = query_engine.process_query(query)
            print(f"Answer: {result.answer}")
            print(f"Confidence: {result.confidence:.2f}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        pytest.fail(f"PDF parsing integration test failed: {e}")

# Remove the if __name__ == "__main__": block
# if __name__ == "__main__":
#     test_pdf_parsing() 