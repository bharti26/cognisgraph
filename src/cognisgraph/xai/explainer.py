import networkx as nx
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..core.knowledge_store import KnowledgeStore
from ..core.query_engine import QueryResult
from .saliency import SaliencyAnalyzer
from .counterfactual import CounterfactualExplainer
from .feature_importance import FeatureImportanceAnalyzer
from .rule_extractor import RuleExtractor

logger = logging.getLogger(__name__)

class GraphExplainer:
    """Provides methods to generate explanations for knowledge graph structures and query results.

    Integrates various analysis components like Saliency, Feature Importance,
    Counterfactuals, and Rule Extraction.
    """

    def __init__(self, knowledge_store: KnowledgeStore):
        """Initializes the GraphExplainer with necessary components.

        Args:
            knowledge_store: The KnowledgeStore instance containing the graph data.
        """
        if not isinstance(knowledge_store, KnowledgeStore):
             raise TypeError("knowledge_store must be an instance of KnowledgeStore")
             
        self.knowledge_store = knowledge_store
        self.graph = knowledge_store.graph
        
        # Initialize analyzer components
        self.saliency_analyzer = SaliencyAnalyzer(self.graph)
        self.feature_analyzer = FeatureImportanceAnalyzer(self.knowledge_store)
        self.counterfactual_explainer = CounterfactualExplainer(self.graph)
        self.rule_extractor = RuleExtractor(self.graph)
        logger.debug("GraphExplainer initialized with analyzers.")

    def explain_query_result(self, query_result: QueryResult) -> Dict[str, Any]:
        """Generates a comprehensive explanation for a given QueryResult.

        Args:
            query_result: The QueryResult object returned by the QueryEngine.

        Returns:
            A dictionary containing different types of explanations:
            - saliency: Importance scores for nodes and paths.
            - feature_importance: Analysis of feature relevance.
            - counterfactuals: Potential changes affecting the result (placeholder).
            - rules: Extracted graph patterns (placeholder).
        """
        if not isinstance(query_result, QueryResult):
             raise TypeError("query_result must be an instance of QueryResult")
             
        logger.info(f"Generating explanation for query: '{query_result.query[:50]}...'")
        evidence_nodes = [item['id'] for item in query_result.evidence if item['type'] == 'entity']
        evidence_edges = [
            (item['source'], item['target']) 
            for item in query_result.evidence 
            if item['type'] == 'relationship'
        ]

        explanation = {}

        # --- Ensure Analyzers use the CURRENT graph --- 
        self.saliency_analyzer.graph = self.knowledge_store.graph
        self.feature_analyzer.graph = self.knowledge_store.graph
        # Update other analyzers if they store self.graph
        if hasattr(self.counterfactual_explainer, 'graph'):
            self.counterfactual_explainer.graph = self.knowledge_store.graph
        if hasattr(self.rule_extractor, 'graph'):
            self.rule_extractor.graph = self.knowledge_store.graph
        # --- End graph update --- 

        try:
            logger.debug("Running Saliency Analysis...")
            explanation['saliency'] = self.saliency_analyzer.analyze(target_nodes=evidence_nodes)
        except Exception as e:
            logger.error(f"Saliency analysis failed: {e}", exc_info=True)
            explanation['saliency'] = {"error": str(e)}

        try:
            logger.debug("Running Feature Importance Analysis...")
            explanation['feature_importance'] = self.feature_analyzer.analyze(entity_ids=evidence_nodes)
        except Exception as e:
            logger.error(f"Feature importance analysis failed: {e}", exc_info=True)
            explanation['feature_importance'] = {"error": str(e)}

        # Placeholder for counterfactuals and rules
        logger.debug("Generating placeholder Counterfactuals and Rules...")
        explanation['counterfactuals'] = self.suggest_counterfactuals(query_result)
        explanation['rules'] = self.extract_rules(evidence_nodes, evidence_edges)

        logger.info("Explanation generation complete.")
        return explanation

    def explain_entity(self, entity_id: str) -> Dict[str, Any]:
        """Generates explanations focused on a specific entity.

        Args:
            entity_id: The ID of the entity to explain.

        Returns:
            A dictionary containing explanations like centrality, community role, etc.
        """
        if entity_id not in self.knowledge_store.entity_index:
             logger.error(f"Cannot explain entity: Entity ID '{entity_id}' not found.")
             return {"error": f"Entity ID '{entity_id}' not found."}
             
        logger.info(f"Generating explanation for entity: {entity_id}")
        explanation = {}

        # --- Ensure Analyzers use the CURRENT graph --- 
        self.saliency_analyzer.graph = self.knowledge_store.graph
        self.feature_analyzer.graph = self.knowledge_store.graph
        # --- End graph update --- 

        try:
            explanation['saliency'] = self.saliency_analyzer.analyze(target_nodes=[entity_id])
        except Exception as e:
            logger.error(f"Saliency analysis failed for entity '{entity_id}': {e}", exc_info=True)
            explanation['saliency'] = {"error": str(e)}
            
        try:
             explanation['feature_importance'] = self.feature_analyzer.analyze(entity_ids=[entity_id])
        except Exception as e:
            logger.error(f"Feature importance analysis failed for entity '{entity_id}': {e}", exc_info=True)
            explanation['feature_importance'] = {"error": str(e)}
        # Add other relevant explanations for a single entity if needed
        return explanation

    def suggest_counterfactuals(self, query_result: QueryResult) -> List[Dict[str, Any]]:
        """Suggests counterfactual changes that might alter the query result (Placeholder).
        
        Args:
            query_result: The original query result.
            
        Returns:
            A list of potential counterfactual explanations.
        """
        # Placeholder implementation - needs actual logic
        logger.warning("suggest_counterfactuals is a placeholder and needs implementation.")
        return [
            {
                "change": "Remove relationship X", 
                "impact": "Answer confidence might decrease."
            }
        ]

    def extract_rules(self, nodes: List[str], edges: List[Tuple[str, str]]) -> List[str]:
        """Extracts graph patterns or rules relevant to the given nodes/edges (Placeholder).
        
        Args:
            nodes: A list of entity IDs involved.
            edges: A list of edge tuples (source_id, target_id) involved.
            
        Returns:
            A list of extracted rules or patterns as strings.
        """
        # Placeholder implementation - needs actual logic
        logger.warning("extract_rules is a placeholder and needs implementation.")
        if nodes or edges:
             return ["Placeholder Rule: High degree nodes are often important."]
        else:
             return ["Placeholder Rule: No specific nodes/edges provided for rule extraction."]

    def analyze_relationships(self, entity_id: str) -> Dict[str, Any]:
        """
        Analyze and explain the relationships of an entity.
        
        Args:
            entity_id: ID of the entity to analyze
            
        Returns:
            Dictionary containing relationship analysis
        """
        relationships = self.knowledge_store.get_relationships(entity_id)
        analysis = {
            "incoming": [],
            "outgoing": [],
            "strength": {},
            "types": {}
        }
        
        for rel in relationships:
            if rel.source == entity_id:
                analysis["outgoing"].append(rel)
            else:
                analysis["incoming"].append(rel)
            
            # Analyze relationship strength
            analysis["strength"][rel.type] = self._calculate_relationship_strength(rel)
            
            # Count relationship types
            analysis["types"][rel.type] = analysis["types"].get(rel.type, 0) + 1
        
        return analysis
    
    def _calculate_relationship_strength(self, relationship) -> float:
        """Calculate the strength of a relationship based on its properties."""
        # This is a simple implementation - can be enhanced based on specific needs
        base_strength = 1.0
        if relationship.properties:
            # Add strength based on properties
            for prop, value in relationship.properties.items():
                if isinstance(value, (int, float)):
                    base_strength += value * 0.1
        return base_strength 