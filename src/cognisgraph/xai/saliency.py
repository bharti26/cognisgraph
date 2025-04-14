"""Saliency analysis module."""

from typing import Dict, Any, List, Optional
import networkx as nx
from cognisgraph.core.knowledge_store import KnowledgeStore
import logging
from datetime import datetime

# Import community detection if available
try:
    import community as community_louvain # python-louvain package
except ImportError:
    community_louvain = None

logger = logging.getLogger(__name__)

class SaliencyAnalyzer:
    """Calculates saliency scores for nodes in a graph, indicating their importance.
    
    Uses various centrality measures (degree, betweenness, closeness, eigenvector)
    and can also compute path importance and community roles.
    """
    
    def __init__(self, knowledge_store: KnowledgeStore):
        """Initializes the analyzer with the graph.

        Args:
            knowledge_store: The KnowledgeStore containing the graph.
        """
        self.knowledge_store = knowledge_store
        self._validate_knowledge_store()
        self.graph = knowledge_store.graph
        self._centrality_cache: Dict[str, Dict[Any, float]] = {}
        self._last_analysis_time: Optional[datetime] = None
        logger.info("SaliencyAnalyzer initialized successfully.")
        logger.debug(f"Initial graph has {len(self.graph.nodes())} nodes and {len(self.graph.edges())} edges")
    
    def _validate_knowledge_store(self):
        """Validate the knowledge store and its graph attribute."""
        if not isinstance(self.knowledge_store, KnowledgeStore):
            logger.error(f"Invalid knowledge store type: {type(self.knowledge_store)}")
            raise TypeError("knowledge_store must be an instance of KnowledgeStore")
            
        if not hasattr(self.knowledge_store, 'graph'):
            logger.error("KnowledgeStore has no graph attribute")
            raise TypeError("KnowledgeStore must have a graph attribute")
            
        if not isinstance(self.knowledge_store.graph, nx.DiGraph):
            logger.error(f"Expected NetworkX DiGraph, got {type(self.knowledge_store.graph)}")
            raise TypeError("KnowledgeStore.graph must be a NetworkX DiGraph")
    
    def analyze(self, target_nodes: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Performs a comprehensive saliency analysis.

        Args:
            target_nodes: Optional list of nodes to focus the analysis on.
                          If None, analyzes the entire graph.

        Returns:
            A dictionary containing:
            - 'centrality_scores': Dictionary mapping node ID to its centrality scores.
            - 'path_importance': Placeholder for path importance scores.
            - 'community_role': Placeholder for community role analysis.
        """
        start_time = datetime.now()
        logger.info(f"Starting saliency analysis. Target nodes: {target_nodes or 'all'}")
        logger.debug(f"Current graph has {len(self.graph.nodes())} nodes and {len(self.graph.edges())} edges")
        
        if not self.graph or len(self.graph.nodes()) == 0:
            logger.warning("Graph is empty, cannot perform saliency analysis.")
            return self._default_analysis()
            
        if target_nodes is not None:
            # Ensure target nodes exist in the graph
            valid_target_nodes = [node for node in target_nodes if node in self.graph]
            if not valid_target_nodes:
                logger.warning(f"None of the target nodes found in the graph. Target nodes: {target_nodes}")
                logger.debug(f"Available nodes in graph: {list(self.graph.nodes())}")
                return self._default_analysis()
            nodes_to_analyze = valid_target_nodes
        else:
            nodes_to_analyze = list(self.graph.nodes())
            
        try:
            centrality_scores = {}
            for node in nodes_to_analyze:
                try:
                    centrality_scores[node] = self._calculate_all_centralities(node)
                except Exception as e:
                    logger.error(f"Failed to calculate centralities for node {node}: {e}", exc_info=True)
                    centrality_scores[node] = self._default_centrality_scores()
            
            # Placeholder for more advanced analyses
            try:
                path_importance = self._analyze_path_importance(nodes_to_analyze)
            except Exception as e:
                logger.error(f"Failed to analyze path importance: {e}", exc_info=True)
                path_importance = {}
            
            try:
                community_role = self._analyze_community_role(nodes_to_analyze)
            except Exception as e:
                logger.error(f"Failed to analyze community roles: {e}", exc_info=True)
                community_role = {}

            analysis_result = {
                "centrality_scores": centrality_scores,
                "path_importance": path_importance,
                "community_role": community_role
            }
            
            self._last_analysis_time = datetime.now()
            analysis_duration = (self._last_analysis_time - start_time).total_seconds()
            logger.info(f"Saliency analysis complete in {analysis_duration:.2f} seconds.")
            logger.debug(f"Analyzed {len(nodes_to_analyze)} nodes")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error during saliency analysis: {e}", exc_info=True)
            return self._default_analysis()
    
    def calculate_centrality(self, entity_id: str) -> Dict[str, float]:
        """
        Calculate various centrality measures for an entity.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            Dictionary of centrality scores
        """
        if not self.graph or entity_id not in self.graph:
            return {
                "degree_centrality": 0.0,
                "betweenness_centrality": 0.0,
                "closeness_centrality": 0.0,
                "eigenvector_centrality": 0.0
            }
        
        try:
            return {
                "degree_centrality": nx.degree_centrality(self.graph).get(entity_id, 0.0),
                "betweenness_centrality": nx.betweenness_centrality(self.graph).get(entity_id, 0.0),
                "closeness_centrality": nx.closeness_centrality(self.graph).get(entity_id, 0.0),
                "eigenvector_centrality": nx.eigenvector_centrality(self.graph).get(entity_id, 0.0)
            }
        except Exception:
            return {
                "degree_centrality": 0.0,
                "betweenness_centrality": 0.0,
                "closeness_centrality": 0.0,
                "eigenvector_centrality": 0.0
            }
    
    def _get_involved_entities(self, result: Any) -> List[str]:
        """Extract entities involved in a query result."""
        entities = []
        
        # Handle QueryResult object
        if hasattr(result, 'evidence'):
            for evidence in result.evidence:
                if evidence.get('type') == 'entity' and 'id' in evidence:
                    entities.append(evidence['id'])
                elif evidence.get('type') == 'relationship':
                    if 'source' in evidence:
                        entities.append(evidence['source'])
                    if 'target' in evidence:
                        entities.append(evidence['target'])
        
        # Handle dictionary result
        elif isinstance(result, dict):
            if 'evidence' in result:
                for evidence in result['evidence']:
                    if evidence.get('type') == 'entity' and 'id' in evidence:
                        entities.append(evidence['id'])
                    elif evidence.get('type') == 'relationship':
                        if 'source' in evidence:
                            entities.append(evidence['source'])
                        if 'target' in evidence:
                            entities.append(evidence['target'])
            elif 'entity' in result:
                entities.append(result['entity'])
            elif 'entities' in result:
                entities.extend(result['entities'])
        
        # Handle list result
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    if item.get('type') == 'entity' and 'id' in item:
                        entities.append(item['id'])
                    elif item.get('type') == 'relationship':
                        if 'source' in item:
                            entities.append(item['source'])
                        if 'target' in item:
                            entities.append(item['target'])
                    elif 'id' in item:
                        entities.append(item['id'])
                    elif 'entity' in item:
                        entities.append(item['entity'])
                    elif 'entities' in item:
                        entities.extend(item['entities'])
        
        # Remove duplicates and empty strings
        return list(set(filter(None, entities)))
    
    def _analyze_path_importance(self, entities: List[str]) -> Dict[str, Any]:
        """Analyze the importance of paths between entities."""
        path_importance = {}
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1 in self.graph and entity2 in self.graph:
                    try:
                        # Find all shortest paths in both directions
                        paths = []
                        try:
                            paths.extend(list(nx.all_shortest_paths(self.graph, entity1, entity2)))
                        except nx.NetworkXNoPath:
                            pass
                            
                        try:
                            paths.extend(list(nx.all_shortest_paths(self.graph, entity2, entity1)))
                        except nx.NetworkXNoPath:
                            pass
                        
                        if paths:
                            # Calculate path importance
                            importance = self._calculate_path_importance(paths)
                            
                            # Store both directions
                            path_importance[f"{entity1}-{entity2}"] = {
                                "paths": paths,
                                "importance": importance
                            }
                            path_importance[f"{entity2}-{entity1}"] = {
                                "paths": paths,
                                "importance": importance
                            }
                    except Exception as e:
                        logger.error(f"Error analyzing path between {entity1} and {entity2}: {e}", exc_info=True)
                        continue
        
        return path_importance
    
    def _analyze_community_role(self, entities: List[str]) -> Dict[str, Any]:
        """Analyze the role of entities in their communities."""
        # Detect communities
        communities = nx.algorithms.community.greedy_modularity_communities(self.graph)
        
        community_roles = {}
        for entity in entities:
            if entity in self.graph:
                # Find which community the entity belongs to
                for i, community in enumerate(communities):
                    if entity in community:
                        # Calculate role within community
                        role = self._calculate_community_role(entity, community)
                        community_roles[entity] = {
                            "community_id": i,
                            "role": role,
                            "community_size": len(community)
                        }
                        break
        
        return community_roles
    
    def _calculate_path_importance(self, paths: List[List[str]]) -> float:
        """Calculate the importance of a set of paths."""
        if not paths:
            return 0.0
        
        # Calculate importance based on multiple factors:
        # 1. Path length (shorter paths are more important)
        # 2. Number of paths (more paths indicate stronger connection)
        # 3. Path diversity (different paths indicate more robust connection)
        
        total_importance = 0.0
        path_lengths = []
        
        for path in paths:
            path_length = len(path) - 1  # Number of edges
            path_lengths.append(path_length)
            # Shorter paths are more important
            total_importance += 1.0 / (path_length + 1)  # +1 to avoid division by zero
        
        # Normalize by number of paths
        if path_lengths:
            avg_length = sum(path_lengths) / len(path_lengths)
            # More paths indicate stronger connection
            path_count_factor = min(1.0, len(paths) / 5.0)  # Cap at 5 paths
            # Shorter average path length is better
            length_factor = 1.0 / (avg_length + 1)
            
            importance = (total_importance / len(paths)) * path_count_factor * length_factor
            return min(1.0, importance)  # Ensure result is between 0 and 1
        
        return 0.0
    
    def _calculate_community_role(self, entity: str, community: set) -> str:
        """Calculate the role of an entity within its community."""
        # Handle communities with only one node
        if len(community) <= 1:
            return "Isolated" # Or "Single-Node Community"

        # Get entity's connections within community
        community_connections = sum(1 for neighbor in self.graph[entity]
                                 if neighbor in community)
        
        # Calculate role based on connection density
        # Denominator is now safe because we checked len(community) > 1
        density = community_connections / (len(community) - 1)
        
        if density > 0.8:
            return "Hub"
        elif density > 0.5:
            return "Connector"
        elif density > 0.2:
            return "Member"
        else:
            return "Peripheral"

    def clear_cache(self):
        """Clears the internal centrality cache."""
        logger.info("Clearing SaliencyAnalyzer centrality cache.")
        self._centrality_cache = {}
        logger.debug("Cache cleared successfully.")

    def _default_centrality_scores(self) -> Dict[str, float]:
        """Returns default centrality scores when calculation fails."""
        return {
            "degree_centrality": 0.0,
            "betweenness_centrality": 0.0,
            "closeness_centrality": 0.0,
            "eigenvector_centrality": 0.0
        }

    def _default_analysis(self) -> Dict[str, Any]:
        """Returns a default analysis when an error occurs."""
        return {
            "centrality_scores": {},
            "path_importance": {},
            "community_role": {}
        }

    def _calculate_all_centralities(self, node: Any) -> Dict[str, float]:
        """Calculate all centrality measures for a node, handling convergence errors."""
        # Check cache first
        if node in self._centrality_cache:
            logger.debug(f"Using cached centrality scores for node {node}")
            return self._centrality_cache[node]
            
        centrality_scores = {}
        
        # Degree (usually safe)
        try:
            centrality_scores["degree_centrality"] = nx.degree_centrality(self.graph).get(node, 0.0)
        except Exception as e:
            logger.error(f"Failed calculating degree centrality for {node}: {e}")
            centrality_scores["degree_centrality"] = 0.0
        
        # Betweenness (can be expensive)
        try:
            # Consider adding k parameter for larger graphs if needed
            centrality_scores["betweenness_centrality"] = nx.betweenness_centrality(self.graph, normalized=True, weight=None).get(node, 0.0)
        except Exception as e:
            logger.error(f"Failed calculating betweenness centrality for {node}: {e}")
            centrality_scores["betweenness_centrality"] = 0.0
        
        # Closeness (usually safe)
        try:
            centrality_scores["closeness_centrality"] = nx.closeness_centrality(self.graph).get(node, 0.0)
        except Exception as e:
            logger.error(f"Failed calculating closeness centrality for {node}: {e}")
            centrality_scores["closeness_centrality"] = 0.0
        
        # Eigenvector (prone to convergence issues)
        try:
            eigenvector_centralities = nx.eigenvector_centrality(self.graph, max_iter=500, tol=1e-05)
            centrality_scores["eigenvector_centrality"] = eigenvector_centralities.get(node, 0.0)
        except nx.PowerIterationFailedConvergence:
            logger.warning(f"Eigenvector centrality did not converge for graph containing node {node}. Returning 0.0.")
            centrality_scores["eigenvector_centrality"] = 0.0
        except Exception as e: # Catch other potential errors
            logger.error(f"Failed calculating eigenvector centrality for {node}: {e}")
            centrality_scores["eigenvector_centrality"] = 0.0
        
        # Cache the results
        self._centrality_cache[node] = centrality_scores
        logger.debug(f"Cached centrality scores for node {node}")
        
        return centrality_scores 