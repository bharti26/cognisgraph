import pytest
from cognisgraph.xai.explainer import GraphExplainer
from cognisgraph.core.knowledge_store import KnowledgeStore

@pytest.fixture
def knowledge_store():
    return KnowledgeStore()

@pytest.fixture
def explainer(knowledge_store):
    return GraphExplainer(knowledge_store)

def test_explain_query_result_success(explainer):
    # Test with a simple query result
    query_result = {
        "status": "success",
        "result": {
            "answer": "The answer is 42",
            "evidence": [
                {"text": "Evidence 1", "source": "doc1", "type": "entity", "id": "entity1"},
                {"text": "Evidence 2", "source": "doc2", "type": "entity", "id": "entity2"}
            ]
        }
    }
    
    explanation = explainer.explain_query_result(query_result)
    assert "saliency" in explanation
    assert "counterfactuals" in explanation

def test_explain_query_result_with_results_nodes(explainer):
    # Test with query result containing results.nodes
    query_result = {
        "status": "success",
        "result": {
            "answer": "The answer is 42",
            "results": {
                "nodes": ["node1", "node2"]
            }
        }
    }
    
    explanation = explainer.explain_query_result(query_result)
    assert "saliency" in explanation
    assert "counterfactuals" in explanation

def test_explain_query_result_error(explainer):
    # Test with an error query result
    query_result = {
        "status": "error",
        "error": "Something went wrong"
    }
    
    explanation = explainer.explain_query_result(query_result)
    assert "error" in explanation

def test_explain_query_result_empty(explainer):
    # Test with an empty query result
    query_result = {}
    
    explanation = explainer.explain_query_result(query_result)
    assert "error" in explanation 