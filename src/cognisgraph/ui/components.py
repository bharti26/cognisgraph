import streamlit as st
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from cognisgraph.core.knowledge_store import Entity, Relationship
import logging
import time
import math

logger = logging.getLogger(__name__)

class FileUploader:
    """Component for uploading files."""
    
    @staticmethod
    def display() -> Optional[List[Any]]:
        """Display file uploader and return uploaded files."""
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=['pdf', 'txt', 'doc', 'docx'],
            accept_multiple_files=True,
            help="Upload your documents to build the knowledge graph"
        )
        
        # Display document information if files are uploaded
        if uploaded_files:
            st.markdown("### Uploaded Documents")
            for file in uploaded_files:
                with st.expander(f"📄 {file.name}", expanded=True):
                    st.markdown(f"**Type:** {file.type}")
                    st.markdown(f"**Size:** {len(file.getvalue()) / 1024:.2f} KB")
                    if file.type == 'application/pdf':
                        st.markdown("**Content:** PDF document")
                    elif file.type == 'text/plain':
                        st.markdown("**Content:** Text document")
                    elif file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                        st.markdown("**Content:** Word document")
        
        return uploaded_files

class QueryInput:
    """Component for query input."""
    
    @staticmethod
    def display() -> str:
        """Display query input and return query string."""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            query = st.text_input(
                "Ask a question",
                placeholder="e.g., What is the capital of France?",
                key="query_input"
            )
        
        with col2:
            submit = st.button(
                "Submit",
                key="submit_button",
                use_container_width=True
            )
        
        # Validate query before returning
        if submit:
            if not query or not query.strip():
                st.error("Please enter a question")
                return ""
            return query.strip()
        return ""

class ResponseDisplay:
    """Component for displaying query responses."""
    
    @staticmethod
    def display(response: str):
        """Display formatted response.
        
        Args:
            response: The response text to display
        """
        st.markdown("### Answer")
        
        # Define maximum length for preview
        MAX_PREVIEW_LENGTH = 500
        
        # Check if response needs truncation
        needs_truncation = len(response) > MAX_PREVIEW_LENGTH
        preview_text = response[:MAX_PREVIEW_LENGTH] + "..." if needs_truncation else response
        
        # Create expander for the answer
        with st.expander("View Answer", expanded=True):
            # Display preview text
            st.markdown(
                f'<div style="font-size: 1.2em; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">{preview_text}</div>',
                unsafe_allow_html=True
            )
            
            # If text was truncated, show a button to view full answer
            if needs_truncation:
                if st.button("Show Full Answer"):
                    st.markdown(
                        f'<div style="font-size: 1.2em; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">{response}</div>',
                        unsafe_allow_html=True
                    )

class KnowledgeGraphViewer:
    """Component for visualizing knowledge graphs."""
    
    def __init__(self, title: str = "Knowledge Graph"):
        """Initialize the viewer.
        
        Args:
            title: Title to display above the graph
        """
        self.title = title
        self._viz_counter = 0  # Instance variable for visualization counter
        self._button_counter = 0  # Instance variable for button counter
    
    def display(self, entities: List[Entity], relationships: List[Relationship], 
                layout: str = "spring", node_size: int = 10, edge_width: float = 1.0):
        """Display the knowledge graph visualization."""
        st.markdown(f"### {self.title}")
        
        # Create two columns for controls and visualization
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Layout selection
            layout = st.selectbox(
                "Layout",
                options=["spring", "circular", "random"],
                index=0
            )
            
            # Node size control
            node_size = st.slider(
                "Node Size",
                min_value=5,
                max_value=30,
                value=10,
                step=1
            )
            
            # Edge width control
            edge_width = st.slider(
                "Edge Width",
                min_value=0.5,
                max_value=3.0,
                value=1.0,
                step=0.1
            )
            
            # Update button with unique key
            button_key = f"update_viz_{self._button_counter}"
            update_clicked = st.button("Update Visualization", key=button_key)
            
            # Increment button counter for next render
            self._button_counter += 1
        
        with col2:
            # Generate a new key for the visualization
            viz_key = f"knowledge_graph_{self._viz_counter}"
            if update_clicked:
                self._viz_counter += 1
            
            try:
                # Create and display the figure
                fig = self.create_figure(entities, relationships, layout, node_size, edge_width)
                st.plotly_chart(fig, use_container_width=True, key=viz_key)
            except Exception as e:
                st.error(f"Error generating visualization: {str(e)}")
    
    @staticmethod
    def create_figure(entities: List[Entity], relationships: List[Relationship],
                     layout: str = "spring", node_size: int = 10, edge_width: float = 1.0) -> go.Figure:
        """Create a Plotly figure for the knowledge graph.
        
        Args:
            entities: List of entities to display
            relationships: List of relationships to display
            layout: Layout algorithm to use
            node_size: Size of nodes in the graph
            edge_width: Width of edges in the graph
            
        Returns:
            Plotly figure object
        """
        # Create empty figure
        fig = go.Figure()
        
        # Create NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for entity in entities:
            G.add_node(entity.id, type=entity.type, name=getattr(entity, 'name', None))
        
        # Add edges
        for rel in relationships:
            if rel.source in G and rel.target in G:
                G.add_edge(rel.source, rel.target, type=rel.type)
        
        # Calculate positions using NetworkX layout algorithms
        if layout == "spring":
            positions = nx.spring_layout(G)
        elif layout == "circular":
            positions = nx.circular_layout(G)
        else:  # random
            positions = nx.random_layout(G)
        
        # Add edges first (so they appear behind nodes)
        for rel in relationships:
            if rel.source in positions and rel.target in positions:
                source_pos = positions[rel.source]
                target_pos = positions[rel.target]
                
                fig.add_trace(go.Scatter(
                    x=[source_pos[0], target_pos[0]],
                    y=[source_pos[1], target_pos[1]],
                    mode='lines',
                    line=dict(width=edge_width, color='gray'),
                    hoverinfo='text',
                    text=f"{rel.type}",
                    showlegend=False
                ))
        
        # Add nodes
        for entity in entities:
            pos = positions[entity.id]
            
            # Count relationships for this entity
            rel_count = sum(1 for r in relationships 
                          if r.source == entity.id or r.target == entity.id)
            
            # Node color based on relationship count
            color = 'lightblue' if rel_count == 0 else 'lightgreen'
            
            # Get entity display name - use name if available, otherwise use type and id
            display_name = getattr(entity, 'name', None)
            if not display_name:
                display_name = f"{entity.type}: {entity.id}"
            
            fig.add_trace(go.Scatter(
                x=[pos[0]],
                y=[pos[1]],
                mode='markers+text',
                marker=dict(
                    size=node_size,
                    color=color,
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                text=[display_name],
                textposition="bottom center",
                hoverinfo='text',
                hovertext=f"Type: {entity.type}<br>ID: {entity.id}",
                showlegend=False
            ))
        
        # Update layout
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            hovermode='closest',
            height=600,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
        return fig

class DocumentViewer:
    """Component for viewing relevant documents."""
    
    @staticmethod
    def display(documents: List[Dict]):
        """Display document snippets with highlights."""
        for doc in documents:
            with st.expander(f"Document: {doc.get('title', 'Untitled')}"):
                st.markdown("### Content")
                content = doc.get('content', '')
                if content:
                    st.markdown(
                        f'<div style="max-height: 300px; overflow-y: auto;">{content}</div>',
                        unsafe_allow_html=True
                    )
                
                if doc.get('highlights'):
                    st.markdown("### Relevant Excerpts")
                    for highlight in doc['highlights']:
                        st.markdown(
                            f'<div class="source-highlight">{highlight}</div>',
                            unsafe_allow_html=True
                        )

class XAIMetrics:
    """Component for displaying XAI metrics and explanations."""
    
    @staticmethod
    def display(metrics: Dict[str, Any]) -> None:
        """Display XAI metrics in a formatted way."""
        st.subheader("Analysis")
        
        # Display confidence score
        if "confidence" in metrics:
            confidence = metrics["confidence"]
            st.metric("Confidence Score", f"{confidence:.2%}")
        
        # Display explanation
        if "explanation" in metrics and metrics["explanation"]:
            st.subheader("Explanation")
            explanation = metrics["explanation"]
            
            # If explanation is a string
            if isinstance(explanation, str):
                st.write(explanation)
            
            # If explanation is a dictionary
            elif isinstance(explanation, dict):
                # Display reasoning steps if present
                if "reasoning_steps" in explanation:
                    st.write("**Reasoning Steps:**")
                    for step in explanation["reasoning_steps"]:
                        st.write(f"- {step}")
                
                # Display sources if present
                if "sources" in explanation:
                    st.write("**Sources:**")
                    for source in explanation["sources"]:
                        st.write(f"- {source}")
                
                # Display context if present
                if "context" in explanation:
                    st.write("**Context:**")
                    st.write(explanation["context"])
                
                # Display additional explanation fields
                for key, value in explanation.items():
                    if key not in ["reasoning_steps", "sources", "context", "confidence"]:
                        st.write(f"**{key.title()}:**")
                        if isinstance(value, list):
                            for item in value:
                                st.write(f"- {item}")
                        else:
                            st.write(str(value))
        
        # Display entity and relationship counts
        if "entities" in metrics and "relationships" in metrics:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Entities", len(metrics["entities"]))
            with col2:
                st.metric("Relationships", len(metrics["relationships"]))
        
        # Display saliency analysis
        if "saliency" in metrics and metrics["saliency"]:
            st.subheader("Saliency Analysis")
            saliency = metrics["saliency"]
            
            if "centrality_scores" in saliency:
                st.write("Node Centrality Scores:")
                centrality_data = []
                for node, scores in saliency["centrality_scores"].items():
                    centrality_data.append({
                        "Node": node,
                        "Degree Centrality": scores.get("degree_centrality", 0.0),
                        "Betweenness Centrality": scores.get("betweenness_centrality", 0.0),
                        "Closeness Centrality": scores.get("closeness_centrality", 0.0),
                        "Eigenvector Centrality": scores.get("eigenvector_centrality", 0.0)
                    })
                st.dataframe(centrality_data)
            
            if "path_importance" in saliency:
                st.write("Path Importance:")
                path_data = []
                for path, data in saliency["path_importance"].items():
                    path_data.append({
                        "Path": path,
                        "Importance": data.get("importance", 0.0),
                        "Number of Paths": len(data.get("paths", []))
                    })
                st.dataframe(path_data)
        
        # Display counterfactuals
        if "counterfactuals" in metrics and metrics["counterfactuals"]:
            st.subheader("Counterfactual Analysis")
            counterfactuals = metrics["counterfactuals"]
            
            if "alternative_paths" in counterfactuals:
                st.write("Alternative Paths:")
                for path in counterfactuals["alternative_paths"]:
                    st.write(f"- {path}")
            
            if "what_if" in counterfactuals:
                st.write("What-If Scenarios:")
                for scenario in counterfactuals["what_if"]:
                    st.write(f"- {scenario}")
        
        # Display feature importance if available
        if "feature_importance" in metrics:
            st.markdown("### Feature Importance")
            feature_imp = metrics["feature_importance"]
            
            if "importance_scores" in feature_imp:
                st.markdown("**Importance Scores:**")
                for feature, score in feature_imp["importance_scores"].items():
                    st.markdown(f"- {feature}: {score:.3f}")
            
            if "ranked_features" in feature_imp:
                st.markdown("**Top Features:**")
                for feature, score in feature_imp["ranked_features"]:
                    st.markdown(f"- {feature}: {score:.3f}")
        
        # Display timing metrics if present
        if "timing" in metrics:
            st.markdown("**Timing Metrics:**")
            for key, value in metrics["timing"].items():
                st.markdown(f"- {key}: {value:.2f}s") 