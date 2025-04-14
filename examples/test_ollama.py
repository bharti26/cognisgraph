import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship
from cognisgraph.nlp.query_engine import QueryEngine

def test_ollama_integration():
    # Initialize knowledge store with some test data
    store = KnowledgeStore()
    
    # Add some test entities
    person1 = Entity(
        id="person1",
        type="Person",
        properties={"name": "John Doe", "age": 30, "occupation": "Software Engineer"}
    )
    person2 = Entity(
        id="person2",
        type="Person",
        properties={"name": "Jane Smith", "age": 28, "occupation": "Data Scientist"}
    )
    company1 = Entity(
        id="company1",
        type="Company",
        properties={"name": "TechCorp", "industry": "Technology"}
    )
    
    store.add_entity(person1)
    store.add_entity(person2)
    store.add_entity(company1)
    
    # Add some relationships
    rel1 = Relationship(
        source="person1",
        target="company1",
        type="works_at",
        properties={}
    )
    rel2 = Relationship(
        source="person2",
        target="company1",
        type="works_at",
        properties={}
    )
    rel3 = Relationship(
        source="person1",
        target="person2",
        type="knows",
        properties={}
    )
    
    store.add_relationship(rel1)
    store.add_relationship(rel2)
    store.add_relationship(rel3)
    
    # Initialize query engine
    query_engine = QueryEngine(store)
    
    # Test queries
    queries = [
        "Who works at TechCorp?",
        "What is John Doe's occupation?",
        "How old is Jane Smith?",
        "Who does John Doe know?"
    ]
    
    # Process each query
    for query in queries:
        print(f"\nQuery: {query}")
        result = query_engine.process_query(query)
        
        if result["status"] == "success":
            print(f"Answer: {result['answer']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Explanation: {result['explanation']}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_ollama_integration() 