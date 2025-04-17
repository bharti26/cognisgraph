import pytest
import pytest_asyncio
import networkx as nx
import plotly.graph_objects as go
from cognisgraph import CognisGraph
from unittest.mock import Mock
import os

# Test PDF path
TEST_PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample.pdf")

@pytest.fixture
def mock_llm():
    """Mock LLM that returns a fixed response."""
    mock = Mock()
    mock.return_value = '''{
        "entities": [
            {
                "id": "doc1",
                "type": "Document",
                "properties": {
                    "name": "test.pdf",
                    "content": "This is a test document"
                }
            },
            {
                "id": "person1",
                "type": "Person",
                "properties": {
                    "name": "John Doe"
                }
            },
            {
                "id": "org1",
                "type": "Organization",
                "properties": {
                    "name": "Test Corp"
                }
            }
        ],
        "relationships": [
            {
                "source": "person1",
                "target": "org1",
                "type": "works_at",
                "properties": {}
            }
        ]
    }'''
    return mock

@pytest_asyncio.fixture
async def cognisgraph(mock_llm, monkeypatch):
    """Create a CognisGraph instance with test components."""
    # Mock OllamaLLM to return our mock for QueryEngine
    monkeypatch.setattr('cognisgraph.nlp.query_engine.OllamaLLM', lambda **kwargs: mock_llm)
    monkeypatch.setattr('cognisgraph.api.endpoints.Ollama', lambda **kwargs: mock_llm)
    
    # Mock PDFParser to return our mock response
    async def mock_parse_pdf(self, file_path):
        return {
            "text": "This is a test document",
            "entities": [
                {
                    "id": "doc1",
                    "type": "Document",
                    "properties": {
                        "name": "test.pdf",
                        "content": "This is a test document"
                    }
                },
                {
                    "id": "person1",
                    "type": "Person",
                    "properties": {
                        "name": "John Doe"
                    }
                },
                {
                    "id": "org1",
                    "type": "Organization",
                    "properties": {
                        "name": "Test Corp"
                    }
                }
            ],
            "relationships": [
                {
                    "source": "person1",
                    "target": "org1",
                    "type": "works_at",
                    "properties": {}
                }
            ]
        }
    
    monkeypatch.setattr('cognisgraph.nlp.pdf_parser.PDFParser.parse_pdf', mock_parse_pdf)
    
    cognis = CognisGraph()
    return cognis

@pytest.fixture
def test_pdf_path():
    """Return the path to the test PDF file."""
    return TEST_PDF_PATH

@pytest.mark.asyncio
async def test_pdf_processing_visualization(test_pdf_path, cognisgraph):
    """Test PDF processing and visualization generation."""
    # Process the PDF
    result = await cognisgraph.add_knowledge(test_pdf_path)
    
    # Verify successful processing
    assert result["status"] == "success", f"PDF processing failed with result: {result}"
    assert "data" in result
    
    # Verify entities were extracted
    assert len(result["data"].get("entities", [])) > 0, "No entities were extracted from the PDF"
    
    # Verify visualization data
    assert "visualization" in result["data"], "Visualization data is missing"
    assert "graph_info" in result["data"], "Graph info is missing"

@pytest.mark.asyncio
async def test_end_to_end_data_consistency(test_pdf_path, cognisgraph):
    """Test that data remains consistent through the entire processing pipeline."""
    # Process the PDF
    result = await cognisgraph.add_knowledge(test_pdf_path)
    
    # Verify successful processing
    assert result["status"] == "success", f"PDF processing failed with result: {result}"
    assert "data" in result
    
    # Get the extracted entities and relationships from the result
    extracted_entities = result["data"].get("entities", [])
    extracted_relationships = result["data"].get("relationships", [])
    
    # Verify entities were extracted
    assert len(extracted_entities) > 0, "No entities were extracted from the PDF"
    
    # Get entities and relationships from knowledge store
    stored_entities = cognisgraph.knowledge_store.get_entities()
    stored_relationships = cognisgraph.knowledge_store.get_relationships()
    
    # Verify knowledge store has all the extracted information
    assert len(stored_entities) == len(extracted_entities), \
        f"Knowledge store has {len(stored_entities)} entities but {len(extracted_entities)} were extracted"
    assert len(stored_relationships) == len(extracted_relationships), \
        f"Knowledge store has {len(stored_relationships)} relationships but {len(extracted_relationships)} were extracted"
    
    # Verify entity properties are preserved
    for entity in extracted_entities:
        # Handle both object and dictionary access
        entity_id = entity.id if hasattr(entity, 'id') else entity['id']
        entity_type = entity.type if hasattr(entity, 'type') else entity['type']
        entity_props = entity.properties if hasattr(entity, 'properties') else entity['properties']
        
        matching_stored = [e for e in stored_entities 
                         if (e.id if hasattr(e, 'id') else e['id']) == entity_id]
        assert len(matching_stored) == 1, f"Entity {entity_id} not found in knowledge store"
        stored_entity = matching_stored[0]
        
        stored_type = stored_entity.type if hasattr(stored_entity, 'type') else stored_entity['type']
        stored_props = stored_entity.properties if hasattr(stored_entity, 'properties') else stored_entity['properties']
        
        assert stored_type == entity_type, \
            f"Entity {entity_id} type mismatch: {stored_type} != {entity_type}"
        assert stored_props == entity_props, \
            f"Entity {entity_id} properties mismatch: {stored_props} != {entity_props}"
    
    # Verify visualization contains all entities and relationships
    vis_data = result["data"]["visualization"]
    assert vis_data is not None, "No visualization data in result"
    
    # Check visualization includes all entities
    vis_nodes = []
    for trace in vis_data.data:
        if hasattr(trace, "text"):
            if isinstance(trace.text, list):
                vis_nodes.extend(trace.text)
            else:
                vis_nodes.append(trace.text)
    
    # Every entity should be represented in the visualization
    for entity in stored_entities:
        entity_id = entity.id if hasattr(entity, 'id') else entity['id']
        entity_found = any(str(entity_id) in str(node) for node in vis_nodes)
        assert entity_found, f"Entity {entity_id} not found in visualization"
    
    # Verify visualization edges match relationships
    vis_edges = []
    for trace in vis_data.data:
        if trace.mode == 'lines':  # This is the edge trace
            vis_edges.extend(trace.text)
    
    # Every relationship should have a corresponding edge
    for rel in stored_relationships:
        rel_source = rel.source if hasattr(rel, 'source') else rel['source']
        rel_target = rel.target if hasattr(rel, 'target') else rel['target']
        edge_id = f"{rel_source}->{rel_target}"
        assert edge_id in vis_edges, f"Relationship {edge_id} not found in visualization edges"

    # Check that all relationships are in the visualization
    visualization = result["data"]["visualization"]
    assert visualization is not None, "Visualization should not be None"
    
    # Check that all entities are in the visualization
    visualization_nodes = []
    for trace in visualization.data:
        if trace.mode == 'markers+text':  # This is the node trace
            visualization_nodes.extend(trace.text)
    
    # Check that all entities are in the visualization nodes
    for entity in stored_entities:
        entity_id = entity.id if hasattr(entity, 'id') else entity['id']
        found = False
        for node_text in visualization_nodes:
            if f"ID: {entity_id}" in node_text:
                found = True
                break
        assert found, f"Entity {entity_id} not found in visualization nodes"
    
    # Check that all relationships are in the visualization
    visualization_edges = []
    for trace in visualization.data:
        if trace.mode == 'lines':  # This is the edge trace
            visualization_edges.extend(trace.text)
    
    # Check that all relationships are in the visualization edges
    for rel in stored_relationships:
        rel_source = rel.source if hasattr(rel, 'source') else rel['source']
        rel_target = rel.target if hasattr(rel, 'target') else rel['target']
        edge_id = f"{rel_source}->{rel_target}"
        assert edge_id in visualization_edges, f"Relationship {edge_id} not found in visualization edges" 