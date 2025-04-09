from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
import logging
from datetime import datetime
from ..core.knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)

class FeatureImportanceAnalyzer:
    """Analyzes the importance of different features (types, properties, relationships)
    within the knowledge graph, potentially focusing on specific entities.
    """
    
    def __init__(self, knowledge_store: KnowledgeStore):
        """Initializes the analyzer.

        Args:
            knowledge_store: The KnowledgeStore instance to analyze.
        """
        if not isinstance(knowledge_store, KnowledgeStore):
            raise TypeError("knowledge_store must be an instance of KnowledgeStore")
        self.knowledge_store = knowledge_store
        self.graph = knowledge_store.graph
        self._centrality_cache = {}
        self._feature_cache = {}
        self._last_update = datetime.now()
        logger.debug("FeatureImportanceAnalyzer initialized.")
    
    def analyze(self, entity_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Performs feature importance analysis.

        Calculates importance scores based on centrality metrics and feature 
        characteristics. Can focus on a subset of entities if provided.

        Args:
            entity_ids: An optional list of entity IDs to focus the analysis on.
                        If None, analyzes features across the entire graph.

        Returns:
            A dictionary containing:
            - 'importance_scores': Scores for different feature categories (type, properties, relationships).
            - 'ranked_features': A list of specific features (like property keys) ranked by importance.
            - 'confidence_scores': Confidence associated with the importance scores.
        """
        logger.info(f"Starting feature importance analysis. Target entities: {entity_ids or 'all'}")

        if entity_ids is not None:
            # Filter the graph or focus calculations on the subgraph induced by entity_ids
            # For simplicity, let's assume calculations consider neighbors as well
            target_nodes = set(entity_ids)
            relevant_nodes = set(entity_ids)
            for node in entity_ids:
                if node in self.graph:
                     # Consider direct neighbors
                     relevant_nodes.update(self.graph.neighbors(node))
                     relevant_nodes.update(self.graph.predecessors(node))
            subgraph = self.graph.subgraph(relevant_nodes)
            logger.debug(f"Analyzing subgraph with {subgraph.number_of_nodes()} nodes and {subgraph.number_of_edges()} edges.")
        else:
            subgraph = self.graph
            logger.debug(f"Analyzing full graph with {subgraph.number_of_nodes()} nodes and {subgraph.number_of_edges()} edges.")

        if subgraph.number_of_nodes() == 0:
             logger.warning("Graph/subgraph for analysis is empty. Returning default scores.")
             return self._default_scores()

        try:
            # --- Calculate Importance Scores --- 
            # These are simplified heuristics. Real implementation might use more complex models.
            
            # Example: Importance based on average degree centrality of nodes with this feature
            type_importance = self._calculate_type_importance(subgraph)
            property_importance = self._calculate_property_importance(subgraph)
            relationship_importance = self._calculate_relationship_importance(subgraph)
            
            importance_scores = {
                "type": type_importance,
                "properties": property_importance,
                "relationships": relationship_importance
            }
            logger.debug(f"Calculated importance scores: {importance_scores}")

            # --- Rank Specific Features --- 
            # Example: Rank specific property keys based on how often they appear or their correlation with centrality
            ranked_features = self._rank_specific_properties(subgraph) # Placeholder for specific property ranking
            logger.debug(f"Ranked features: {ranked_features}")

            # --- Calculate Confidence --- 
            # Example: Confidence based on the size of the graph/subgraph analyzed
            confidence = min(1.0, subgraph.number_of_nodes() / 100.0) # Arbitrary scaling
            confidence_scores = {
                "type": confidence * 0.9, # Assign slightly different confidences
                "properties": confidence * 0.8,
                "relationships": confidence * 0.85
            }
            logger.debug(f"Calculated confidence scores: {confidence_scores}")

            return {
                "importance_scores": importance_scores,
                "ranked_features": ranked_features,
                "confidence_scores": confidence_scores
            }
            
        except Exception as e:
            logger.error(f"Error during feature importance analysis: {e}", exc_info=True)
            # Return default or error structure
            return {
                 "error": f"Analysis failed: {e}",
                 **self._default_scores() # Provide default structure on error
            }

    def _calculate_type_importance(self, graph: nx.DiGraph) -> float:
        """Placeholder: Calculate importance score for entity types."""
        # Example: Could be based on frequency, diversity, or correlation with centrality
        if graph.number_of_nodes() == 0: return 0.0
        num_types = len(set(nx.get_node_attributes(graph, 'type').values()))
        return min(1.0, num_types / 10.0) # Simple heuristic

    def _calculate_property_importance(self, graph: nx.DiGraph) -> float:
        """Placeholder: Calculate importance score for node properties."""
        # Example: Based on average number of properties per node
        if graph.number_of_nodes() == 0: return 0.0
        total_props = sum(len(data.get('properties', {})) for _, data in graph.nodes(data=True))
        avg_props = total_props / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0
        return min(1.0, avg_props / 5.0) # Simple heuristic

    def _calculate_relationship_importance(self, graph: nx.DiGraph) -> float:
        """Placeholder: Calculate importance score for relationships."""
        # Example: Based on graph density or average degree
        if graph.number_of_nodes() == 0: return 0.0
        avg_degree = sum(d for n, d in graph.degree()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0
        return min(1.0, avg_degree / 10.0) # Simple heuristic

    def _rank_specific_properties(self, graph: nx.DiGraph) -> List[Tuple[str, float]]:
        """Placeholder: Rank specific property keys by importance."""
        # Example: Rank by frequency of appearance
        prop_counts: Dict[str, int] = {}
        for _, data in graph.nodes(data=True):
            for key in data.get('properties', {}).keys():
                prop_counts[key] = prop_counts.get(key, 0) + 1
        
        if not prop_counts: return []
        
        max_count = max(prop_counts.values()) if prop_counts else 1
        ranked = sorted(
            [(key, count / max_count) for key, count in prop_counts.items()], 
            key=lambda item: item[1], 
            reverse=True
        )
        return ranked[:5] # Return top 5
        
    def _default_scores(self) -> Dict[str, Any]:
         """Returns a default structure when analysis cannot be performed."""
         return {
             "importance_scores": {"type": 0.0, "properties": 0.0, "relationships": 0.0},
             "ranked_features": [],
             "confidence_scores": {"type": 0.0, "properties": 0.0, "relationships": 0.0}
         }

    def calculate_importance(self, entity: str) -> Dict[str, float]:
        """
        Calculate the importance of features for a given entity.
        
        Args:
            entity: The entity to analyze
            
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not entity or entity not in self.graph:
            logger.warning(f"Invalid entity: {entity}")
            return {}
        
        try:
            # Get entity data
            entity_data = self.knowledge_store.get_entity(entity)
            if not entity_data:
                return {}
            
            # Initialize importance scores
            importance_scores = {}
            
            # Calculate importance based on different metrics
            importance_scores["degree_centrality"] = self._calculate_degree_importance(entity)
            importance_scores["betweenness_centrality"] = self._calculate_betweenness_importance(entity)
            importance_scores["closeness_centrality"] = self._calculate_closeness_importance(entity)
            importance_scores["eigenvector_centrality"] = self._calculate_eigenvector_importance(entity)
            
            # Calculate feature-specific importance
            for feature, value in entity_data.properties.items():
                if isinstance(value, (str, int, float)):
                    importance_scores[f"feature_{feature}"] = self._calculate_feature_importance(
                        entity, feature, value
                    )
            
            # Calculate feature combination importance
            importance_scores.update(self._calculate_feature_combinations(entity_data))
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Error calculating importance for entity {entity}: {str(e)}")
            return {}
    
    def _calculate_degree_importance(self, entity: str) -> float:
        """Calculate importance based on degree centrality."""
        if entity not in self.graph:
            return 0.0
        try:
            if entity in self._centrality_cache:
                return self._centrality_cache[entity]["degree"]
            score = len(self.graph[entity]) / (len(self.graph) - 1)
            self._centrality_cache[entity] = {"degree": score}
            return score
        except Exception as e:
            logger.error(f"Error calculating degree importance: {str(e)}")
            return 0.0
    
    def _calculate_betweenness_importance(self, entity: str) -> float:
        """Calculate importance based on betweenness centrality."""
        if entity not in self.graph:
            return 0.0
        try:
            if entity in self._centrality_cache:
                return self._centrality_cache[entity]["betweenness"]
            score = nx.betweenness_centrality(self.graph)[entity]
            self._centrality_cache[entity]["betweenness"] = score
            return score
        except Exception as e:
            logger.error(f"Error calculating betweenness importance: {str(e)}")
            return 0.0
    
    def _calculate_closeness_importance(self, entity: str) -> float:
        """Calculate importance based on closeness centrality."""
        if entity not in self.graph:
            return 0.0
        try:
            if entity in self._centrality_cache:
                return self._centrality_cache[entity]["closeness"]
            score = nx.closeness_centrality(self.graph)[entity]
            self._centrality_cache[entity]["closeness"] = score
            return score
        except Exception as e:
            logger.error(f"Error calculating closeness importance: {str(e)}")
            return 0.0
    
    def _calculate_eigenvector_importance(self, entity: str) -> float:
        """Calculate importance based on eigenvector centrality."""
        if entity not in self.graph:
            return 0.0
        try:
            if entity in self._centrality_cache:
                return self._centrality_cache[entity]["eigenvector"]
            score = nx.eigenvector_centrality(self.graph)[entity]
            self._centrality_cache[entity]["eigenvector"] = score
            return score
        except Exception as e:
            logger.error(f"Error calculating eigenvector importance: {str(e)}")
            return 0.0
    
    def _calculate_feature_importance(self, entity: str, feature: str, value: Any) -> float:
        """
        Calculate the importance of a specific feature.
        
        Args:
            entity: The entity being analyzed
            feature: The feature name
            value: The feature value
            
        Returns:
            Importance score for the feature
        """
        cache_key = f"{entity}_{feature}_{value}"
        if cache_key in self._feature_cache:
            return self._feature_cache[cache_key]
        
        try:
            # Count how many other entities share this feature value
            count = 0
            total = 0
            
            for node in self.graph.nodes():
                node_data = self.knowledge_store.get_entity(node)
                if node_data and feature in node_data.properties:
                    total += 1
                    if node_data.properties[feature] == value:
                        count += 1
            
            score = count / total if total > 0 else 0.0
            self._feature_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {str(e)}")
            return 0.0

    def _calculate_feature_combinations(self, entity_data: Any) -> Dict[str, float]:
        """
        Calculate importance of feature combinations.
        
        Args:
            entity_data: The entity data
            
        Returns:
            Dictionary of feature combination importance scores
        """
        combinations = {}
        features = list(entity_data.properties.items())
        
        for i in range(len(features)):
            for j in range(i + 1, len(features)):
                feat1, val1 = features[i]
                feat2, val2 = features[j]
                key = f"combination_{feat1}_{feat2}"
                combinations[key] = self._calculate_feature_combination_importance(
                    feat1, val1, feat2, val2
                )
        
        return combinations

    def _calculate_feature_combination_importance(
        self,
        feat1: str,
        val1: Any,
        feat2: str,
        val2: Any
    ) -> float:
        """Calculate importance of a feature combination."""
        cache_key = f"{feat1}_{val1}_{feat2}_{val2}"
        if cache_key in self._feature_cache:
            return self._feature_cache[cache_key]
        
        try:
            count = 0
            total = 0
            
            for node in self.graph.nodes():
                node_data = self.knowledge_store.get_entity(node)
                if (node_data and 
                    feat1 in node_data.properties and 
                    feat2 in node_data.properties):
                    total += 1
                    if (node_data.properties[feat1] == val1 and 
                        node_data.properties[feat2] == val2):
                        count += 1
            
            score = count / total if total > 0 else 0.0
            self._feature_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"Error calculating feature combination importance: {str(e)}")
            return 0.0

    def clear_cache(self):
        """Clear the cached calculations."""
        self._centrality_cache = {}
        self._feature_cache = {}
        self._last_update = datetime.now()
        logger.info("Cache cleared") 