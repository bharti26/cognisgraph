import pytest
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship
from cognisgraph.core.query_engine import QueryEngine

@pytest.fixture
def sample_knowledge_store():
    """Create a knowledge store with sample data."""
    store = KnowledgeStore()
    
    # Add sample entities
    person1 = Entity(
        id="person1",
        type="Person",
        properties={"name": "John", "age": 30, "occupation": "Engineer"}
    )
    person2 = Entity(
        id="person2",
        type="Person",
        properties={"name": "Alice", "age": 28, "occupation": "Scientist"}
    )
    company = Entity(
        id="company1",
        type="Company",
        properties={"name": "TechCorp", "industry": "Technology"}
    )
    
    store.add_entity(person1)
    store.add_entity(person2)
    store.add_entity(company)
    
    # Add sample relationships
    works_at1 = Relationship(
        source="person1",
        target="company1",
        type="works_at",
        properties={"role": "Senior Engineer", "since": 2020}
    )
    works_at2 = Relationship(
        source="person2",
        target="company1",
        type="works_at",
        properties={"role": "Research Scientist", "since": 2021}
    )
    colleague = Relationship(
        source="person1",
        target="person2",
        type="colleague",
        properties={"department": "R&D"}
    )
    
    store.add_relationship(works_at1)
    store.add_relationship(works_at2)
    store.add_relationship(colleague)
    
    return store

def test_query_engine_initialization(sample_knowledge_store):
    """Test that the query engine initializes correctly."""
    engine = QueryEngine(sample_knowledge_store)
    assert engine is not None
    assert engine.knowledge_store == sample_knowledge_store

def test_works_at_query(sample_knowledge_store):
    """Test the 'Who works at TechCorp?' query."""
    engine = QueryEngine(sample_knowledge_store)
    result = engine.process_query("Who works at TechCorp?")
    
    # Check that we got a result
    assert result is not None
    assert result.answer != "I don't have enough information to answer that question."
    
    # Check that the answer contains both employees
    assert "John" in result.answer
    assert "Alice" in result.answer
    assert "TechCorp" in result.answer
    
    # Check that the evidence contains both relationships
    assert len(result.evidence) >= 2
    works_at_relationships = [
        e for e in result.evidence 
        if e.get("type") == "relationship" and e.get("relationship_type") == "works_at"
    ]
    assert len(works_at_relationships) == 2
    
    # Check that the explanation contains saliency analysis
    assert result.explanation is not None
    assert "saliency" in result.explanation
    assert "centrality_scores" in result.explanation["saliency"]
    assert "path_importance" in result.explanation["saliency"]
    assert "community_role" in result.explanation["saliency"]

def test_entity_properties(sample_knowledge_store):
    """Test that entity properties are correctly retrieved."""
    engine = QueryEngine(sample_knowledge_store)
    result = engine.process_query("What is John's occupation?")
    
    assert result is not None
    assert "Engineer" in result.answer
    assert "John" in result.answer

def test_relationship_properties(sample_knowledge_store):
    """Test that relationship properties are correctly retrieved."""
    engine = QueryEngine(sample_knowledge_store)
    result = engine.process_query("How long has Alice been working at TechCorp?")
    
    assert result is not None
    assert "2021" in result.answer
    assert "Alice" in result.answer
    assert "TechCorp" in result.answer 