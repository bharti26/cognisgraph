from typing import Dict, Any, List, Optional
import networkx as nx
from ..core.knowledge_store import KnowledgeStore
import logging

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
        self.graph = knowledge_store.graph
        # Cache for centrality measures to avoid recomputation
        self._centrality_cache: Dict[str, Dict[Any, float]] = {}
        logger.debug("SaliencyAnalyzer initialized.")
    
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
        logger.info(f"Starting saliency analysis. Target nodes: {target_nodes or 'all'}")
        if target_nodes is not None:
            # Ensure target nodes exist in the graph
            valid_target_nodes = [node for node in target_nodes if node in self.graph]
            if not valid_target_nodes:
                logger.warning("None of the target nodes found in the graph.")
                return self._default_analysis()
            nodes_to_analyze = valid_target_nodes
            # Analyze centrality in the context of the full graph for better comparison
            graph_context = self.graph
        else:
            nodes_to_analyze = list(self.graph.nodes())
            if not nodes_to_analyze:
                 logger.warning("Graph is empty, cannot perform saliency analysis.")
                 return self._default_analysis()
            graph_context = self.graph
            
        if not nodes_to_analyze:
             logger.warning("No valid nodes to analyze.") # Should not happen if graph wasn't empty
             return self._default_analysis()

        try:
            centrality_scores = {}
            for node in nodes_to_analyze:
                 centrality_scores[node] = self._calculate_all_centralities(node, graph_context)
            
            # Placeholder for more advanced analyses
            path_importance = self._analyze_path_importance(nodes_to_analyze, graph_context)
            community_role = self._analyze_community_role(nodes_to_analyze, graph_context)

            analysis_result = {
                "centrality_scores": centrality_scores,
                "path_importance": path_importance,
                "community_role": community_role
            }
            logger.info("Saliency analysis complete.")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error during saliency analysis: {e}", exc_info=True)
            return {
                "error": f"Analysis failed: {e}",
                **self._default_analysis()
            }
    
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
    
    def _analyze_path_importance(self, entities: List[str], graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze the importance of paths between entities."""
        path_importance = {}
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1 in graph and entity2 in graph:
                    try:
                        # Find all shortest paths
                        paths = list(nx.all_shortest_paths(graph, entity1, entity2))
                        
                        # Calculate path importance
                        importance = self._calculate_path_importance(paths)
                        
                        path_importance[f"{entity1}-{entity2}"] = {
                            "paths": paths,
                            "importance": importance
                        }
                    except nx.NetworkXNoPath:
                        continue
        
        return path_importance
    
    def _analyze_community_role(self, entities: List[str], graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze the role of entities in their communities."""
        # Detect communities
        communities = nx.algorithms.community.greedy_modularity_communities(graph)
        
        community_roles = {}
        for entity in entities:
            if entity in graph:
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
        
        # Simple implementation: importance inversely proportional to path length
        # Can be enhanced with more sophisticated metrics
        total_importance = 0.0
        for path in paths:
            path_length = len(path) - 1  # Number of edges
            total_importance += 1.0 / path_length
        
        return total_importance / len(paths)
    
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

    def _default_analysis(self) -> Dict[str, Any]:
        """Returns a default analysis when an error occurs."""
        return {
            "centrality_scores": {},
            "path_importance": {},
            "community_role": {}
        }

    def _calculate_all_centralities(self, node: Any, graph: nx.DiGraph) -> Dict[str, float]:
        """Calculate all centrality measures for a node, handling convergence errors."""
        centrality_scores = {}
        
        # Degree (usually safe)
        try:
            centrality_scores["degree_centrality"] = nx.degree_centrality(graph).get(node, 0.0)
        except Exception as e:
            logger.error(f"Failed calculating degree centrality for {node}: {e}")
            centrality_scores["degree_centrality"] = 0.0
        
        # Betweenness (can be expensive)
        try:
            # Consider adding k parameter for larger graphs if needed
            centrality_scores["betweenness_centrality"] = nx.betweenness_centrality(graph, normalized=True, weight=None).get(node, 0.0)
        except Exception as e:
            logger.error(f"Failed calculating betweenness centrality for {node}: {e}")
            centrality_scores["betweenness_centrality"] = 0.0
        
        # Closeness (usually safe)
        try:
            centrality_scores["closeness_centrality"] = nx.closeness_centrality(graph).get(node, 0.0)
        except Exception as e:
            logger.error(f"Failed calculating closeness centrality for {node}: {e}")
            centrality_scores["closeness_centrality"] = 0.0
        
        # Eigenvector (prone to convergence issues)
        try:
            eigenvector_centralities = nx.eigenvector_centrality(graph, max_iter=500, tol=1e-05)
            centrality_scores["eigenvector_centrality"] = eigenvector_centralities.get(node, 0.0)
        except nx.PowerIterationFailedConvergence:
            logger.warning(f"Eigenvector centrality did not converge for graph containing node {node}. Returning 0.0.")
            centrality_scores["eigenvector_centrality"] = 0.0
        except Exception as e: # Catch other potential errors
            logger.error(f"Failed calculating eigenvector centrality for {node}: {e}")
            centrality_scores["eigenvector_centrality"] = 0.0
        
        return centrality_scores 