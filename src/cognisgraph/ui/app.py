import streamlit as st
import os
import asyncio
from cognisgraph import CognisGraph
from cognisgraph.config import Config
import logging
import tempfile
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import pandas as pd
import json
import networkx as nx
from functools import lru_cache
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temp directory for uploaded files
TEMP_UPLOAD_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Cache centrality calculations
@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_centrality_measures(_G):
    """Calculate and cache centrality measures for a graph.
    
    Args:
        _G: NetworkX graph (prefixed with underscore to prevent hashing)
    """
    try:
        # Basic centrality measures that are more stable
        betweenness = nx.betweenness_centrality(_G)
        closeness = nx.closeness_centrality(_G)
        
        # Try eigenvector centrality with more robust parameters
        try:
            # First try with standard parameters
            eigenvector = nx.eigenvector_centrality(_G, max_iter=1000, tol=1e-8)
            logger.info("Eigenvector centrality converged with standard parameters")
        except nx.PowerIterationFailedConvergence as e:
            logger.warning(f"First eigenvector centrality attempt failed: {str(e)}")
            try:
                # If that fails, try with more iterations and relaxed tolerance
                eigenvector = nx.eigenvector_centrality(_G, max_iter=2000, tol=1e-6)
                logger.info("Eigenvector centrality converged with relaxed parameters")
            except nx.PowerIterationFailedConvergence as e:
                logger.warning(f"Second eigenvector centrality attempt failed: {str(e)}")
                try:
                    # If that fails, try with even more relaxed parameters
                    eigenvector = nx.eigenvector_centrality(_G, max_iter=5000, tol=1e-4)
                    logger.info("Eigenvector centrality converged with very relaxed parameters")
                except nx.PowerIterationFailedConvergence as e:
                    logger.warning(f"All eigenvector centrality attempts failed: {str(e)}")
                    # Use a weighted combination of degree and pagerank as fallback
                    degree = nx.degree_centrality(_G)
                    pagerank = nx.pagerank(_G)
                    eigenvector = {
                        node: 0.6 * pagerank[node] + 0.4 * degree[node]
                        for node in _G.nodes()
                    }
                    logger.info("Using weighted fallback for eigenvector centrality")
        
        # Add additional stable centrality measures
        degree = nx.degree_centrality(_G)
        pagerank = nx.pagerank(_G)
        
        # Log graph statistics for debugging
        logger.info(f"Graph statistics - Nodes: {len(_G.nodes())}, Edges: {len(_G.edges())}")
        logger.info(f"Graph density: {nx.density(_G):.4f}")
        
        return {
            "betweenness": betweenness,
            "closeness": closeness,
            "eigenvector": eigenvector,
            "degree": degree,
            "pagerank": pagerank
        }
    except Exception as e:
        logger.error(f"Error calculating centrality measures: {str(e)}")
        # Fallback to simple degree centrality if other measures fail
        try:
            degree = nx.degree_centrality(_G)
            logger.warning("Using degree centrality as fallback for all measures")
            return {
                "betweenness": degree,
                "closeness": degree,
                "eigenvector": degree,
                "degree": degree,
                "pagerank": degree
            }
        except Exception as e2:
            logger.error(f"Even degree centrality failed: {str(e2)}")
            # Return empty dictionaries to prevent visualization errors
            return {
                "betweenness": {},
                "closeness": {},
                "eigenvector": {},
                "degree": {},
                "pagerank": {}
            }

# Initialize CognisGraph once and cache it
@st.cache_resource
def init_cognisgraph():
    """Initialize CognisGraph with default configuration."""
    config = Config()
    return CognisGraph(config)

async def process_pdf(cognisgraph, file_path):
    """Process PDF file asynchronously."""
    try:
        # Check if file exists and is a PDF
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}
        
        if not file_path.lower().endswith('.pdf'):
            return {"status": "error", "message": "Unsupported file type. Please upload a PDF file."}
        
        result = await cognisgraph.add_knowledge(file_path)
        if result["status"] == "success":
            return {"status": "success", "data": result.get("data", {})}
        else:
            return {"status": "error", "message": result.get("message", "Error processing PDF")}
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return {"status": "error", "message": str(e)}

async def process_query(cognisgraph, query):
    """Process query asynchronously."""
    try:
        if not query or not query.strip():
            return {"status": "error", "message": "Query cannot be empty"}
        
        result = await cognisgraph.query(query)
        if result["status"] == "success":
            return {
                "status": "success",
                "data": {
                    "answer": result["data"]["answer"],
                    "confidence": result["data"].get("confidence", None),
                    "explanation": result["data"].get("explanation", None)
                }
            }
        else:
            return {"status": "error", "message": result.get("message", "Error processing query")}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"status": "error", "message": str(e)}

async def generate_visualization(cognisgraph):
    """Generate visualization asynchronously."""
    try:
        result = await cognisgraph.visualize()
        if result["status"] == "success":
            return result  # Return the complete result instead of just data
        else:
            return {"status": "error", "message": result.get("message", "Error generating visualization")}
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return {"status": "error", "message": str(e)}

def main():
    # Set page config
    st.set_page_config(
        page_title="CognisGraph",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state for graph data if not exists
    if 'graph_data' not in st.session_state:
        st.session_state.graph_data = None
    if 'processed_file' not in st.session_state:
        st.session_state.processed_file = None
    if 'viz_data' not in st.session_state:
        st.session_state.viz_data = None
    if 'entities' not in st.session_state:
        st.session_state.entities = None
    if 'relationships' not in st.session_state:
        st.session_state.relationships = None
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            background-color: #f5f5f5;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            background-color: #4CAF50;
            color: white;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .metric-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150", width=150)
        st.title("CognisGraph")
        st.markdown("---")
        
        # Navigation
        selected = option_menu(
            menu_title=None,
            options=["Home", "Knowledge Graph", "Query", "Settings"],
            icons=["house", "graph-up", "search", "gear"],
            default_index=0,
        )
    
    # Initialize CognisGraph
    cognisgraph = init_cognisgraph()
    
    if selected == "Home":
        st.header("Welcome to CognisGraph")
        st.markdown("""
        CognisGraph is an intelligent knowledge graph system that helps you:
        - Extract and visualize knowledge from PDF documents
        - Query and explore relationships between entities
        - Gain insights through interactive visualizations
        """)
        
        # Quick start section
        with st.expander("Quick Start Guide", expanded=True):
            st.markdown("""
            1. Upload a PDF document in the Knowledge Graph tab
            2. Process the document to extract entities and relationships
            3. Explore the knowledge graph through visualization
            4. Query the knowledge base for specific information
            """)
    
    elif selected == "Knowledge Graph":
        st.header("Knowledge Graph")
        
        # File upload section with modern design
        with st.container():
            st.subheader("Upload and Process PDF")
            uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="file_uploader")
            
            if uploaded_file is not None:
                # Save the uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_path = tmp_file.name
                
                # Process the PDF with a modern button
                if st.button("Process PDF", key="process_pdf"):
                    with st.spinner("Processing PDF..."):
                        result = asyncio.run(process_pdf(cognisgraph, tmp_path))
                        
                        if result["status"] == "success":
                            st.success("PDF processed successfully!")
                            
                            # Store the processed data in session state
                            st.session_state.graph_data = result.get("data", {})
                            st.session_state.processed_file = uploaded_file.name
                            
                            # Store entities and relationships in session state
                            if "entities" in result.get("data", {}):
                                st.session_state.entities = result["data"]["entities"]
                            if "relationships" in result.get("data", {}):
                                st.session_state.relationships = result["data"]["relationships"]
                            
                            # Display entities in a modern card layout
                            if "entities" in result.get("data", {}):
                                with st.expander("Extracted Entities", expanded=False):
                                    for entity in result["data"]["entities"]:
                                        with st.container():
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>{entity['id']}</h3>
                                                <p><strong>Type:</strong> {entity['type']}</p>
                                                {f"<p><strong>Properties:</strong> {entity['properties']}</p>" if entity.get("properties") else ""}
                                            </div>
                                            """, unsafe_allow_html=True)
                            
                            # Display relationships in a modern card layout
                            if "relationships" in result.get("data", {}):
                                with st.expander("Extracted Relationships", expanded=False):
                                    for rel in result["data"]["relationships"]:
                                        with st.container():
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>{rel['source']} → {rel['target']}</h3>
                                                <p><strong>Type:</strong> {rel['type']}</p>
                                                {f"<p><strong>Properties:</strong> {rel['properties']}</p>" if rel.get("properties") else ""}
                                            </div>
                                            """, unsafe_allow_html=True)
                            
                            # Generate and display visualization with modern layout
                            with st.spinner("Generating visualization..."):
                                viz_result = asyncio.run(generate_visualization(cognisgraph))
                                if viz_result["status"] == "success":
                                    # Store visualization data in session state
                                    st.session_state.viz_data = viz_result
                                    
                                    # Display the Plotly figure in a container
                                    with st.container():
                                        st.plotly_chart(viz_result["data"]["figure"], use_container_width=True)
                                    
                                    # Display graph metrics in a modern card layout
                                    with st.expander("Graph Metrics", expanded=False):
                                        metrics = viz_result["data"]["graph_info"]
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>Nodes</h3>
                                                <p style="font-size: 24px;">{metrics["num_nodes"]}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>Edges</h3>
                                                <p style="font-size: 24px;">{metrics["num_edges"]}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col2:
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>Density</h3>
                                                <p style="font-size: 24px;">{metrics['density']:.3f}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>Average Degree</h3>
                                                <p style="font-size: 24px;">{metrics['average_degree']:.2f}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col3:
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>Components</h3>
                                                <p style="font-size: 24px;">{metrics["components"]}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <h3>Connected</h3>
                                                <p style="font-size: 24px;">{"Yes" if metrics["is_connected"] else "No"}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    # Additional Visualizations
                                    with st.expander("Graph Analysis", expanded=True):
                                        try:
                                            # Validate graph data
                                            if "data" not in viz_result or "graph" not in viz_result["data"]:
                                                st.error("No graph data available for visualization")
                                                return
                                            
                                            # Get the NetworkX graph from the visualization result
                                            G = viz_result["data"]["graph"]
                                            
                                            if not isinstance(G, nx.Graph):
                                                st.error("Invalid graph format")
                                                return
                                            
                                            if len(G.nodes()) == 0:
                                                st.warning("Graph is empty - no nodes to visualize")
                                                return
                                            
                                            # Node Type Distribution
                                            st.subheader("Node Type Distribution")
                                            try:
                                                node_types = {}
                                                for node in G.nodes():
                                                    node_type = G.nodes[node].get("type", "unknown")
                                                    node_types[node_type] = node_types.get(node_type, 0) + 1
                                                
                                                if not node_types:
                                                    st.warning("No node types found")
                                                else:
                                                    fig_node_types = go.Figure(data=[go.Pie(
                                                        labels=list(node_types.keys()),
                                                        values=list(node_types.values()),
                                                        hole=.3
                                                    )])
                                                    fig_node_types.update_layout(
                                                        title="Distribution of Node Types",
                                                        showlegend=True
                                                    )
                                                    st.plotly_chart(fig_node_types, use_container_width=True)
                                            except Exception as e:
                                                logger.error(f"Error creating node type distribution: {str(e)}")
                                                st.error("Failed to create node type distribution")
                                            
                                            # Relationship Type Distribution
                                            st.subheader("Relationship Type Distribution")
                                            try:
                                                rel_types = {}
                                                for edge in G.edges(data=True):
                                                    rel_type = edge[2].get("type", "unknown")
                                                    rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
                                                
                                                if not rel_types:
                                                    st.warning("No relationship types found")
                                                else:
                                                    fig_rel_types = go.Figure(data=[go.Bar(
                                                        x=list(rel_types.keys()),
                                                        y=list(rel_types.values())
                                                    )])
                                                    fig_rel_types.update_layout(
                                                        title="Distribution of Relationship Types",
                                                        xaxis_title="Relationship Type",
                                                        yaxis_title="Count"
                                                    )
                                                    st.plotly_chart(fig_rel_types, use_container_width=True)
                                            except Exception as e:
                                                logger.error(f"Error creating relationship type distribution: {str(e)}")
                                                st.error("Failed to create relationship type distribution")
                                            
                                            # Degree Distribution
                                            st.subheader("Degree Distribution")
                                            try:
                                                degrees = [G.degree(node) for node in G.nodes()]
                                                if not degrees:
                                                    st.warning("No degree data available")
                                                else:
                                                    fig_degree = go.Figure(data=[go.Histogram(
                                                        x=degrees,
                                                        nbinsx=20
                                                    )])
                                                    fig_degree.update_layout(
                                                        title="Node Degree Distribution",
                                                        xaxis_title="Degree",
                                                        yaxis_title="Count"
                                                    )
                                                    st.plotly_chart(fig_degree, use_container_width=True)
                                            except Exception as e:
                                                logger.error(f"Error creating degree distribution: {str(e)}")
                                                st.error("Failed to create degree distribution")
                                            
                                            # Centrality Measures
                                            st.subheader("Centrality Analysis")
                                            try:
                                                centrality_measures = calculate_centrality_measures(G)
                                                if not centrality_measures:
                                                    st.warning("No centrality measures available")
                                                else:
                                                    centrality_data = []
                                                    for node in G.nodes():
                                                        centrality_data.append({
                                                            "node": node,
                                                            "degree": centrality_measures["degree"].get(node, 0),
                                                            "betweenness": centrality_measures["betweenness"].get(node, 0),
                                                            "closeness": centrality_measures["closeness"].get(node, 0),
                                                            "eigenvector": centrality_measures["eigenvector"].get(node, 0),
                                                            "pagerank": centrality_measures["pagerank"].get(node, 0)
                                                        })
                                                    
                                                    df_centrality = pd.DataFrame(centrality_data)
                                                    
                                                    # Scatter plot of centrality measures
                                                    fig_centrality = go.Figure()
                                                    fig_centrality.add_trace(go.Scatter(
                                                        x=df_centrality["degree"],
                                                        y=df_centrality["betweenness"],
                                                        mode='markers',
                                                        text=df_centrality["node"],
                                                        marker=dict(
                                                            size=df_centrality["eigenvector"] * 20,
                                                            color=df_centrality["closeness"],
                                                            colorscale='Viridis',
                                                            showscale=True
                                                        )
                                                    ))
                                                    fig_centrality.update_layout(
                                                        title="Centrality Measures Scatter Plot",
                                                        xaxis_title="Degree Centrality",
                                                        yaxis_title="Betweenness Centrality",
                                                        hovermode='closest'
                                                    )
                                                    st.plotly_chart(fig_centrality, use_container_width=True)
                                            except Exception as e:
                                                logger.error(f"Error creating centrality analysis: {str(e)}")
                                                st.error("Failed to create centrality analysis")
                                            
                                        except Exception as e:
                                            logger.error(f"Error in graph analysis: {str(e)}")
                                            st.error("An error occurred while analyzing the graph")
                                else:
                                    st.error(f"Error generating visualization: {viz_result.get('message', 'Unknown error')}")
                        else:
                            st.error(f"Error processing PDF: {result.get('message', 'Unknown error')}")
                    
                    # Clean up temporary file
                    os.unlink(tmp_path)
            elif st.session_state.graph_data is not None:
                # Display previously processed data
                st.info(f"Currently loaded file: {st.session_state.processed_file}")
                st.markdown("---")
                
                # Export options
                with st.expander("Export Data", expanded=False):
                    st.subheader("Export Options")
                    export_format = st.radio(
                        "Select export format:",
                        ["JSON", "CSV", "Graph"],
                        horizontal=True
                    )
                    
                    if export_format == "JSON":
                        # Export entities
                        if hasattr(st.session_state, 'entities'):
                            entities_json = json.dumps(st.session_state.entities, indent=2)
                            st.download_button(
                                label="Download Entities (JSON)",
                                data=entities_json,
                                file_name="entities.json",
                                mime="application/json"
                            )
                        
                        # Export relationships
                        if hasattr(st.session_state, 'relationships'):
                            relationships_json = json.dumps(st.session_state.relationships, indent=2)
                            st.download_button(
                                label="Download Relationships (JSON)",
                                data=relationships_json,
                                file_name="relationships.json",
                                mime="application/json"
                            )
                    
                    elif export_format == "CSV":
                        # Export entities
                        if hasattr(st.session_state, 'entities'):
                            # Convert entities to DataFrame
                            entities_df = pd.DataFrame(st.session_state.entities)
                            # Convert properties to string if they exist
                            if 'properties' in entities_df.columns:
                                entities_df['properties'] = entities_df['properties'].apply(lambda x: json.dumps(x) if x else '')
                            # Convert to CSV
                            entities_csv = entities_df.to_csv(index=False)
                            st.download_button(
                                label="Download Entities (CSV)",
                                data=entities_csv,
                                file_name="entities.csv",
                                mime="text/csv"
                            )
                        
                        # Export relationships
                        if hasattr(st.session_state, 'relationships'):
                            # Convert relationships to DataFrame
                            relationships_df = pd.DataFrame(st.session_state.relationships)
                            # Convert properties to string if they exist
                            if 'properties' in relationships_df.columns:
                                relationships_df['properties'] = relationships_df['properties'].apply(lambda x: json.dumps(x) if x else '')
                            # Convert to CSV
                            relationships_csv = relationships_df.to_csv(index=False)
                            st.download_button(
                                label="Download Relationships (CSV)",
                                data=relationships_csv,
                                file_name="relationships.csv",
                                mime="text/csv"
                            )
                    
                    else:  # Graph format
                        if 'viz_data' in st.session_state and 'data' in st.session_state.viz_data and 'graph' in st.session_state.viz_data['data']:
                            G = st.session_state.viz_data['data']['graph']
                            
                            # Export as PNG
                            if st.button("Export as PNG"):
                                try:
                                    # Create a temporary file
                                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                                        # Draw the graph
                                        plt.figure(figsize=(12, 8))
                                        pos = nx.spring_layout(G)
                                        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                                               node_size=500, font_size=8, font_weight='bold')
                                        plt.savefig(tmp.name, format='png', dpi=300, bbox_inches='tight')
                                        plt.close()
                                        
                                        # Read the file and create download button
                                        with open(tmp.name, 'rb') as f:
                                            st.download_button(
                                                label="Download Graph (PNG)",
                                                data=f,
                                                file_name="graph.png",
                                                mime="image/png"
                                            )
                                except Exception as e:
                                    st.error(f"Error exporting graph as PNG: {str(e)}")
                            
                            # Export as SVG
                            if st.button("Export as SVG"):
                                try:
                                    # Create a temporary file
                                    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
                                        # Draw the graph
                                        plt.figure(figsize=(12, 8))
                                        pos = nx.spring_layout(G)
                                        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                                               node_size=500, font_size=8, font_weight='bold')
                                        plt.savefig(tmp.name, format='svg', bbox_inches='tight')
                                        plt.close()
                                        
                                        # Read the file and create download button
                                        with open(tmp.name, 'rb') as f:
                                            st.download_button(
                                                label="Download Graph (SVG)",
                                                data=f,
                                                file_name="graph.svg",
                                                mime="image/svg+xml"
                                            )
                                except Exception as e:
                                    st.error(f"Error exporting graph as SVG: {str(e)}")
                            
                            # Export as GraphML
                            if st.button("Export as GraphML"):
                                try:
                                    # Create a temporary file
                                    with tempfile.NamedTemporaryFile(suffix='.graphml', delete=False) as tmp:
                                        # Write the graph to GraphML format
                                        nx.write_graphml(G, tmp.name)
                                        
                                        # Read the file and create download button
                                        with open(tmp.name, 'rb') as f:
                                            st.download_button(
                                                label="Download Graph (GraphML)",
                                                data=f,
                                                file_name="graph.graphml",
                                                mime="application/xml"
                                            )
                                except Exception as e:
                                    st.error(f"Error exporting graph as GraphML: {str(e)}")
                        else:
                            st.warning("No graph data available for export")
                
                # Display stored entities
                if hasattr(st.session_state, 'entities'):
                    with st.expander("Extracted Entities", expanded=False):
                        for entity in st.session_state.entities:
                            with st.container():
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{entity['id']}</h3>
                                    <p><strong>Type:</strong> {entity['type']}</p>
                                    {f"<p><strong>Properties:</strong> {entity['properties']}</p>" if entity.get("properties") else ""}
                                </div>
                                """, unsafe_allow_html=True)
                
                # Display stored relationships
                if hasattr(st.session_state, 'relationships'):
                    with st.expander("Extracted Relationships", expanded=False):
                        for rel in st.session_state.relationships:
                            with st.container():
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{rel['source']} → {rel['target']}</h3>
                                    <p><strong>Type:</strong> {rel['type']}</p>
                                    {f"<p><strong>Properties:</strong> {rel['properties']}</p>" if rel.get("properties") else ""}
                                </div>
                                """, unsafe_allow_html=True)
                
                # Display the stored visualization
                if 'viz_data' in st.session_state:
                    viz_result = st.session_state.viz_data
                    with st.container():
                        st.plotly_chart(viz_result["data"]["figure"], use_container_width=True)
                    
                    # Display graph metrics
                    with st.expander("Graph Metrics", expanded=False):
                        metrics = viz_result["data"]["graph_info"]
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Nodes</h3>
                                <p style="font-size: 24px;">{metrics["num_nodes"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Edges</h3>
                                <p style="font-size: 24px;">{metrics["num_edges"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Density</h3>
                                <p style="font-size: 24px;">{metrics['density']:.3f}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Average Degree</h3>
                                <p style="font-size: 24px;">{metrics['average_degree']:.2f}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Components</h3>
                                <p style="font-size: 24px;">{metrics["components"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Connected</h3>
                                <p style="font-size: 24px;">{"Yes" if metrics["is_connected"] else "No"}</p>
                            </div>
                            """, unsafe_allow_html=True)
    
    elif selected == "Query":
        st.header("Query Knowledge Graph")
        
        # Check if there's processed data available
        if st.session_state.graph_data is None:
            st.warning("Please process a PDF file in the Knowledge Graph tab first.")
            return
        
        # Modern query input with suggestions
        query = st.text_input(
            "Enter your query:",
            placeholder="e.g., Find all people who work at TechCorp",
            help="Type your question about the knowledge graph here"
        )
        
        if query and st.button("Search", key="search_button"):
            with st.spinner("Processing query..."):
                result = asyncio.run(process_query(cognisgraph, query))
                
                if result["status"] == "success":
                    st.success("Query processed successfully!")
                    
                    # Display answer in a modern card
                    answer_data = result["data"]
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2>Answer</h2>
                        <p style="font-size: 18px;">{answer_data['answer']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show confidence with a modern progress bar
                    if answer_data.get("confidence"):
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Confidence</h3>
                            <div style="background-color: #f0f0f0; border-radius: 5px; padding: 5px;">
                                <div style="background-color: #4CAF50; width: {float(answer_data['confidence']) * 100}%; height: 20px; border-radius: 5px;"></div>
                            </div>
                            <p style="text-align: center; margin-top: 5px;">{answer_data['confidence']:.2%}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show explanation in a modern card
                    if answer_data.get("explanation"):
                        with st.expander("Explanation", expanded=False):
                            st.markdown(f"""
                            <div class="metric-card">
                                {answer_data["explanation"]}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error(f"Error processing query: {result.get('message', 'Unknown error')}")
    
    elif selected == "Settings":
        st.header("Settings")
        st.markdown("Configure your CognisGraph settings here.")
        # Add settings options here

if __name__ == "__main__":
    main() 