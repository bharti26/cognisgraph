from typing import Any, Dict, Optional, List
import logging
import networkx as nx
import plotly.graph_objects as go
from pydantic import BaseModel, Field
from cognisgraph.agents.base_agent import BaseAgent
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship
from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)

class VisualizationInput(BaseModel):
    """Input data for visualization."""
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    method: str = Field(default="plotly")
    output_path: Optional[str] = None

class VisualizationOutput(BaseModel):
    """Output data for visualization."""
    status: str = Field(default="success")
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    explanation: Optional[str] = None

class VisualizationAgent(BaseAgent[nx.Graph]):
    """Agent responsible for graph visualization and layout management."""
    
    def __init__(
        self,
        knowledge_store: Optional[KnowledgeStore] = None,
        query_engine: Optional[Any] = None
    ):
        """Initialize the visualization agent.
        
        Args:
            knowledge_store: Optional shared knowledge store instance
            query_engine: Optional query engine instance (not used by this agent)
        """
        super().__init__(knowledge_store, query_engine)
        self.visualizer = None
        self.state_graph = StateGraph(dict)  # Initialize with empty state
        logger.info("VisualizationAgent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and create visualizations.

        Args:
            input_data: Dictionary containing entities and relationships

        Returns:
            Dictionary containing visualization results
        """
        try:
            # Check if knowledge store is available
            if self.knowledge_store is None:
                return VisualizationOutput(
                    status="error",
                    message="No knowledge store available"
                ).dict()

            # Parse and validate input data
            if isinstance(input_data, dict):
                if "type" in input_data and "content" in input_data:
                    # Handle input from orchestrator
                    input_data = input_data["content"]
                elif "entities" not in input_data and "relationships" not in input_data:
                    # Try to get entities and relationships from knowledge store
                    input_data = {
                        "entities": self.knowledge_store.get_entities(),
                        "relationships": self.knowledge_store.get_relationships()
                    }

            # Convert input entities to Entity objects if needed
            entities = []
            for entity in input_data.get("entities", []):
                if isinstance(entity, Entity):
                    entities.append(entity)
                elif isinstance(entity, dict):
                    try:
                        entities.append(Entity(**entity))
                    except Exception as e:
                        logger.warning(f"Failed to convert entity: {str(e)}")
                        continue
                else:
                    logger.warning(f"Invalid entity format: {entity}")

            # Convert input relationships to Relationship objects if needed
            relationships = []
            for rel in input_data.get("relationships", []):
                if isinstance(rel, Relationship):
                    relationships.append(rel)
                elif isinstance(rel, dict):
                    try:
                        relationships.append(Relationship(**rel))
                    except Exception as e:
                        logger.warning(f"Failed to convert relationship: {str(e)}")
                        continue
                else:
                    logger.warning(f"Invalid relationship format: {rel}")

            # Create visualization input
            viz_input = VisualizationInput(
                entities=entities,
                relationships=relationships,
                method=input_data.get("method", "plotly"),
                output_path=input_data.get("output_path")
            )
            
            # Validate entities
            valid_entities = []
            for entity in viz_input.entities:
                if not isinstance(entity, Entity):
                    logger.warning(f"Invalid entity format: {entity}")
                    continue
                valid_entities.append(entity)

            if not valid_entities:
                return VisualizationOutput(
                    status="error",
                    message="No valid entities found for visualization"
                ).dict()

            # Create graph visualization
            G = nx.DiGraph()
            
            # Add nodes with properties
            for entity in valid_entities:
                try:
                    # Combine type and properties for node attributes
                    node_attrs = {
                        "type": entity.type,
                        "name": entity.properties.get("name", entity.id),
                        **entity.properties
                    }
                    G.add_node(entity.id, **node_attrs)
                except Exception as e:
                    logger.warning(f"Failed to add node {entity.id}: {str(e)}")
                    continue
            
            # Add edges with properties
            valid_relationships = []
            for rel in viz_input.relationships:
                if not isinstance(rel, Relationship):
                    logger.warning(f"Invalid relationship format: {rel}")
                    continue
                if rel.source not in G or rel.target not in G:
                    logger.warning(f"Relationship references non-existent entity: {rel}")
                    continue
                try:
                    edge_attrs = {
                        "type": rel.type,
                        **rel.properties
                    }
                    G.add_edge(rel.source, rel.target, **edge_attrs)
                    valid_relationships.append(rel)
                except Exception as e:
                    logger.warning(f"Failed to add edge {rel.source}->{rel.target}: {str(e)}")
                    continue

            if not valid_relationships:
                return VisualizationOutput(
                    status="error",
                    message="No valid relationships found for visualization"
                ).dict()
            
            try:
                # Create plotly figure
                pos = nx.spring_layout(G)
                
                # Create edge trace
                edge_x = []
                edge_y = []
                edge_text = []
                edge_customdata = []
                for edge in G.edges(data=True):
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_info = edge[2]
                    edge_id = f"{edge[0]}->{edge[1]}"
                    edge_text.extend([
                        edge_id,  # First line must be exactly the edge ID
                        edge_id,  # Repeat edge ID for middle point
                        edge_id   # Repeat edge ID for end point
                    ])
                    edge_customdata.extend([[edge[0], edge[1]], [None, None], [None, None]])
                
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1.5, color='#888'),
                    hoverinfo='text',
                    text=edge_text,
                    mode='lines',
                    customdata=edge_customdata
                )
                
                # Create node trace
                node_x = []
                node_y = []
                node_text = []
                node_colors = []
                node_types = []
                
                # Calculate node centrality (with fallback options)
                try:
                    centrality = nx.degree_centrality(G)
                except Exception as e:
                    logger.warning(f"Failed to calculate degree centrality: {str(e)}")
                    # Fallback to simple degree if centrality fails
                    centrality = {node: len(list(G.neighbors(node))) / max(1, len(G.nodes()) - 1) for node in G.nodes()}
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_data = G.nodes[node]
                    node_text.append(
                        f"ID: {node}<br>" +
                        f"Name: {node_data.get('name', node)}<br>" +
                        f"Type: {node_data.get('type', 'unknown')}<br>" +
                        f"Centrality: {centrality[node]:.3f}<br>" +
                        "<br>".join(f"{k}: {v}" for k, v in node_data.items() if k not in ['type', 'name'])
                    )
                    node_colors.append(centrality[node])
                    node_types.append(node_data.get('type', 'unknown'))
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    text=node_text,
                    marker=dict(
                        showscale=True,
                        colorscale='YlGnBu',
                        reversescale=True,
                        color=node_colors,
                        size=15,
                        colorbar=dict(
                            thickness=15,
                            title='Node Centrality',
                            xanchor='left'
                        ),
                        line_width=2
                    )
                )

                # Create figure
                fig = go.Figure(data=[edge_trace, node_trace],
                              layout=go.Layout(
                                  title=dict(
                                      text='Knowledge Graph Visualization',
                                      font=dict(size=16)
                                  ),
                                  showlegend=False,
                                  hovermode='closest',
                                  margin=dict(b=20, l=5, r=5, t=40),
                                  annotations=[dict(
                                      text="",
                                      showarrow=False,
                                      xref="paper", yref="paper",
                                      x=0.005, y=-0.002
                                  )],
                                  xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                  yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                              ))

                # Calculate comprehensive graph metrics
                graph_metrics = {
                    "basic": {
                        "num_nodes": len(G.nodes()),
                        "num_edges": len(G.edges()),
                        "density": nx.density(G),
                        "average_degree": sum(dict(G.degree()).values()) / len(G.nodes()) if len(G.nodes()) > 0 else 0,
                        "is_connected": nx.is_connected(G.to_undirected()) if len(G.nodes()) > 0 else False,
                        "components": nx.number_connected_components(G.to_undirected()) if len(G.nodes()) > 0 else 0
                    },
                    "centrality": {
                        "degree": nx.degree_centrality(G),
                        "betweenness": nx.betweenness_centrality(G),
                        "closeness": nx.closeness_centrality(G),
                        "eigenvector": {}
                    },
                    "node_types": {},
                    "relationship_types": {},
                    "saliency": {}
                }

                # Calculate eigenvector centrality with fallback
                try:
                    # First try with default parameters
                    graph_metrics["centrality"]["eigenvector"] = nx.eigenvector_centrality(G, max_iter=1000)
                except nx.PowerIterationFailedConvergence:
                    try:
                        # Try with increased max_iter and tolerance
                        graph_metrics["centrality"]["eigenvector"] = nx.eigenvector_centrality(
                            G, max_iter=5000, tol=1e-6
                        )
                    except nx.PowerIterationFailedConvergence:
                        # If still fails, use degree centrality as fallback
                        logger.warning("Eigenvector centrality failed to converge, using degree centrality as fallback")
                        graph_metrics["centrality"]["eigenvector"] = graph_metrics["centrality"]["degree"]
                except Exception as e:
                    logger.warning(f"Error calculating eigenvector centrality: {str(e)}, using degree centrality as fallback")
                    graph_metrics["centrality"]["eigenvector"] = graph_metrics["centrality"]["degree"]

                # Calculate node type distribution
                for node in G.nodes():
                    node_type = G.nodes[node].get('type', 'unknown')
                    graph_metrics["node_types"][node_type] = graph_metrics["node_types"].get(node_type, 0) + 1

                # Calculate relationship type distribution
                for edge in G.edges(data=True):
                    rel_type = edge[2].get('type', 'unknown')
                    graph_metrics["relationship_types"][rel_type] = graph_metrics["relationship_types"].get(rel_type, 0) + 1

                # Calculate saliency scores
                for node in G.nodes():
                    node_data = G.nodes[node]
                    if 'saliency' in node_data:
                        graph_metrics["saliency"][node] = node_data['saliency']

                # Generate explanation
                explanation = self._generate_explanation(graph_metrics)

                # Create visualization output
                return VisualizationOutput(
                    status="success",
                    data={
                        "figure": fig,
                        "graph_info": graph_metrics["basic"]
                    },
                    metrics=graph_metrics,
                    explanation=explanation
                ).dict()

            except Exception as e:
                logger.error(f"Error creating visualization: {str(e)}")
                return VisualizationOutput(
                    status="error",
                    message=f"Error creating visualization: {str(e)}"
                ).dict()

        except Exception as e:
            logger.error(f"Error in visualization process: {str(e)}", exc_info=True)
            return VisualizationOutput(
                status="error",
                message=f"Visualization failed: {str(e)}"
            ).dict()

    def get_layout_options(self) -> List[str]:
        """Get available layout options.
        
        Returns:
            List of available layout algorithms
        """
        return ["spring", "circular", "random", "shell", "spectral"]

    def update_layout(self, layout: str) -> Dict[str, Any]:
        """Update the graph layout.
        
        Args:
            layout: Name of the layout algorithm to use
            
        Returns:
            Dictionary containing updated visualization
        """
        if layout not in self.get_layout_options():
            return VisualizationOutput(
                status="error",
                message=f"Invalid layout option: {layout}"
            ).dict()
            
        try:
            # Update layout and return new visualization
            # TODO: Implement layout update logic
            return VisualizationOutput(
                status="success",
                message=f"Layout updated to {layout}"
            ).dict()
            
        except Exception as e:
            logger.error(f"Error updating layout: {str(e)}")
            return VisualizationOutput(
                status="error",
                message=f"Error updating layout: {str(e)}"
            ).dict()

    def _generate_explanation(self, metrics: Dict[str, Any]) -> str:
        """Generate a natural language explanation of the graph metrics."""
        explanation = []
        
        # Basic graph statistics
        basic = metrics["basic"]
        explanation.append(
            f"The knowledge graph contains {basic['num_nodes']} nodes and {basic['num_edges']} relationships, "
            f"with an average degree of {basic['average_degree']:.2f}. "
            f"The graph has a density of {basic['density']:.3f}."
        )
        
        # Connectivity information
        if basic["is_connected"]:
            explanation.append("The graph is fully connected.")
        else:
            explanation.append(f"The graph consists of {basic['components']} connected components.")
        
        # Node type distribution
        node_types = metrics["node_types"]
        if node_types:
            explanation.append("Node type distribution:")
            for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
                explanation.append(f"- {node_type}: {count} nodes")
        
        # Relationship type distribution
        rel_types = metrics["relationship_types"]
        if rel_types:
            explanation.append("Relationship type distribution:")
            for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
                explanation.append(f"- {rel_type}: {count} relationships")
        
        # Centrality analysis
        centrality = metrics["centrality"]
        if centrality["degree"]:
            # Degree centrality is always available
            top_nodes = sorted(centrality["degree"].items(), key=lambda x: x[1], reverse=True)[:3]
            explanation.append("Most central nodes (by degree):")
            for node, score in top_nodes:
                explanation.append(f"- {node}: {score:.3f}")
            
            # Add eigenvector centrality if available and different from degree
            if centrality["eigenvector"] and centrality["eigenvector"] != centrality["degree"]:
                top_eigen = sorted(centrality["eigenvector"].items(), key=lambda x: x[1], reverse=True)[:3]
                explanation.append("Most influential nodes (by eigenvector centrality):")
                for node, score in top_eigen:
                    explanation.append(f"- {node}: {score:.3f}")
        
        # Saliency analysis
        saliency = metrics["saliency"]
        if saliency:
            top_salient = sorted(saliency.items(), key=lambda x: x[1], reverse=True)[:3]
            explanation.append("Most salient nodes:")
            for node, score in top_salient:
                explanation.append(f"- {node}: {score:.3f}")
        
        return "\n".join(explanation) 