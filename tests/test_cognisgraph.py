import pytest
from cognisgraph import CognisGraph
from cognisgraph.exceptions import (
    KnowledgeError, QueryError, VisualizationError, WorkflowError
)
import os
from cognisgraph.core.knowledge_store import Entity, Relationship

def test_initialization():
    """Test CognisGraph initialization."""
    # Test with default config
    cg = CognisGraph()
    assert cg is not None
    
    # Test with custom config
    config = {
        "debug": True,
        "visualization": {
            "default_method": "networkx"
        }
    }
    cg = CognisGraph(config)
    assert cg.config.debug is True
    assert cg.config.visualization.default_method == "networkx"

def test_add_knowledge():
    """Test adding knowledge to the graph."""
    cg = CognisGraph()
    
    # Test adding single knowledge
    knowledge = {
        "entity": "Python",
        "type": "Programming Language",
        "properties": {"created": 1991}
    }
    assert cg.add_knowledge(knowledge) is True
    
    # Test adding multiple knowledge items
    knowledge_list = [
        {
            "entity": "Guido van Rossum",
            "type": "Person",
            "properties": {"occupation": "Programmer"}
        },
        {
            "entity": "Python Software Foundation",
            "type": "Organization",
            "properties": {"founded": 2001}
        }
    ]
    assert cg.add_knowledge(knowledge_list) is True
    
    # Test invalid knowledge
    with pytest.raises(KnowledgeError):
        cg.add_knowledge({"invalid": "data"})

def test_query():
    """Test querying the knowledge graph."""
    cg = CognisGraph()
    
    # Add some knowledge first
    knowledge = {
        "entity": "Python",
        "type": "Programming Language",
        "properties": {"created": 1991}
    }
    cg.add_knowledge(knowledge)
    
    # Test valid query
    result = cg.query("When was Python created?")
    assert result is not None
    
    # Test invalid query
    with pytest.raises(QueryError):
        cg.query("")

def test_workflow():
    """Test running workflows."""
    cg = CognisGraph()
    
    knowledge = {
        "entity": "Python",
        "type": "Programming Language",
        "properties": {"created": 1991}
    }
    
    # Test valid workflow
    result = cg.run_workflow(knowledge, "When was Python created?")
    assert result is not None
    
    # Test invalid workflow
    with pytest.raises(WorkflowError):
        cg.run_workflow({}, "")

def test_visualization():
    """Test visualization methods."""
    cg = CognisGraph()
    
    # Add some knowledge first
    knowledge = {
        "entity": "Python",
        "type": "Programming Language",
        "properties": {"created": 1991}
    }
    cg.add_knowledge(knowledge)
    
    # Test each visualization method
    methods = ["networkx", "plotly", "pyvis", "graphviz"]
    for method in methods:
        output_path = f"test_{method}"
        if method == "pyvis":
            output_path += ".html"
        elif method == "graphviz":
            pass # graphviz automatically adds .png
        # Add other extensions if needed for other methods
        
        cg.visualize(method=method, output_path=output_path)
        # Basic check: Does the output file exist?
        if method == "graphviz":
            # Graphviz adds .png, check for that
            assert os.path.exists(output_path + ".png"), f"Output file {output_path}.png not created for {method}"
            os.remove(output_path + ".png") # Clean up
        elif method != "networkx": # NetworkX shows plot, doesn't save by default in this test setup
             assert os.path.exists(output_path), f"Output file {output_path} not created for {method}"
             os.remove(output_path) # Clean up

def test_get_entity():
    """Test retrieving entities."""
    cg = CognisGraph()
    
    # Add an entity
    knowledge = {
        "entity": "Python",
        "type": "Programming Language",
        "properties": {"created": 1991}
    }
    cg.add_knowledge(knowledge)
    
    # Test getting existing entity
    entity = cg.get_entity("Python")
    assert entity is not None
    assert entity.id == "Python"
    
    # Test getting non-existent entity
    assert cg.get_entity("NonExistent") is None

def test_get_relationships():
    """Test retrieving relationships."""
    cg = CognisGraph()
    
    # Define entities as dicts suitable for add_knowledge
    python_knowledge = {
        "entity": "Python", 
        "type": "Programming Language", 
        "properties": {"created": 1991}
    }
    guido_knowledge = {
        "entity": "Guido van Rossum", 
        "type": "Person", 
        "properties": {}
    }
    # Add entities using add_knowledge
    cg.add_knowledge(python_knowledge)
    cg.add_knowledge(guido_knowledge)

    # Now define and add the relationship knowledge
    relationship_knowledge = {
        "entity": "Python", # Source entity ID must match an existing entity
        "type": "Programming Language", # Can be omitted if entity exists, or match existing
        "properties": {}, # Can be omitted if entity exists
        "relationships": [
            {
                "target": "Guido van Rossum", # Target entity ID must match an existing entity
                "type": "created_by",
                "properties": {"year": 1991}
            }
        ]
    }
    cg.add_knowledge(relationship_knowledge) # This should now successfully add the relationship
    
    # Test getting relationships
    relationships_python = cg.get_relationships("Python")
    assert len(relationships_python) == 1
    assert relationships_python[0].type == "created_by"
    assert relationships_python[0].target == "Guido van Rossum"

    relationships_guido = cg.get_relationships("Guido van Rossum")
    assert len(relationships_guido) == 1
    assert relationships_guido[0].type == "created_by"
    assert relationships_guido[0].source == "Python"

# Add a test for add_knowledge with relationships where target doesn't exist
def test_add_knowledge_missing_target():
    """Test adding relationship via add_knowledge when target doesn't exist."""
    cg = CognisGraph()
    # Add source entity
    cg.add_knowledge({"entity": "Source", "type": "Test", "properties": {}})
    
    # Attempt to add relationship pointing to non-existent target
    knowledge_with_bad_rel = {
        "entity": "Source",
        "relationships": [
            {
                "target": "NonExistentTarget",
                "type": "points_to",
                "properties": {}
            }
        ]
    }
    # Expect add_relationship within KnowledgeStore to log an error and return False,
    # but add_knowledge currently doesn't explicitly raise KnowledgeError for this.
    # Let's assert that the relationship wasn't actually added.
    cg.add_knowledge(knowledge_with_bad_rel)
    source_relationships = cg.get_relationships("Source")
    assert len(source_relationships) == 0, "Relationship should not be added if target doesn't exist" 