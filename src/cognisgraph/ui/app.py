import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, Any, List

# Use absolute imports
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship
from cognisgraph.core.query_engine import QueryEngine
from cognisgraph.xai.explainer import GraphExplainer
from cognisgraph.xai.saliency import SaliencyAnalyzer
from cognisgraph.xai.counterfactual import CounterfactualExplainer
from cognisgraph.parsers.pdf_parser import PDFParser

import tempfile
import os
# import sys # No longer needed
import logging
import numpy as np
import requests
import json

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="CognisGraph Explorer",
    page_icon="🧠",
    layout="wide"
)

# Use absolute imports now that the package is installed
# from cognisgraph import CognisGraph # This is redundant if using the UI class structure below
# from cognisgraph.core.query_engine import QueryResult # QueryResult is used within QueryEngine methods
# from cognisgraph.utils.file_watcher import FileWatcher # Not used in this class structure

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- UI Class --- 

class CognisGraphUI:
    """Streamlit UI for interacting with CognisGraph."""
    
    # Type hint components for clarity
    knowledge_store: KnowledgeStore
    query_engine: QueryEngine
    explainer: GraphExplainer
    saliency_analyzer: SaliencyAnalyzer
    counterfactual_explainer: CounterfactualExplainer
    pdf_parser: PDFParser

    def __init__(self, knowledge_store: KnowledgeStore, query_engine: QueryEngine):
        """Initializes the UI with core components."""
        self.knowledge_store = knowledge_store
        self.query_engine = query_engine
        # Initialize XAI components using the provided store/engine
        # Assuming GraphExplainer might need query_engine too, adjust if needed
        self.explainer = GraphExplainer(knowledge_store) 
        self.saliency_analyzer = SaliencyAnalyzer(knowledge_store.graph) # Saliency takes the graph
        self.counterfactual_explainer = CounterfactualExplainer(knowledge_store.graph) # Counterfactual takes graph
        self.pdf_parser = PDFParser()
        logger.info("CognisGraphUI initialized.")
        
        # Initialize session state
        if 'query_result' not in st.session_state:
            st.session_state.query_result = None
        if 'pdf_processing_log' not in st.session_state:
            st.session_state.pdf_processing_log = []
        if 'uploaded_pdf_store' not in st.session_state:
            st.session_state.uploaded_pdf_store = None
        
    def run(self):
        """Run the Streamlit app, including navigation and page rendering."""
        # Add custom CSS
        st.markdown("""
            <style>
            .main {
                padding: 2rem;
            }
            .stButton>button {
                width: 100%;
            }
            .info-box {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
            }
            .info-box h4 {
                margin-top: 0;
                color: #1a73e8;
            }
            .stMetric > div:nth-child(2) {
                 font-size: 1.1rem; /* Slightly smaller confidence value */
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.title("🧠 CognisGraph Explorer")
        st.markdown("""
            Welcome to CognisGraph Explorer! This tool helps you explore and understand knowledge graphs.
            Use the sidebar to navigate between different features.
        """)
        
        # Sidebar for navigation
        st.sidebar.title("Navigation")
        page_options = {
            "Ask a Question": self._show_query_page,
            "Explore Items": self._show_entity_explorer,
            "Graph Insights": self._show_xai_dashboard,
            "Add PDF Data": self._show_pdf_upload_page
        }
        
        selected_page_name = st.sidebar.radio(
            "Go to", 
            list(page_options.keys()), 
            key="nav", 
            help="Select a section to navigate"
        )
        
        # Render the selected page
        page_function = page_options[selected_page_name]
        page_function() # Call the corresponding method
    
    def _show_query_page(self):
        """Show the query interface."""
        st.header("Ask a Question")
        st.caption("Enter a question in plain English to query the knowledge graph.")
        
        # Define help text including examples
        query_help_text = ("""
Ask any question about the knowledge graph. Examples:
- What are the main concepts?
- Show relationships for 'Python'
- Connection between 'John Doe' and 'TechCorp Inc'?
- List all 'Person' items
""")

        # Query input with placeholder and updated help text
        query = st.text_area(
            "Enter your question:",
            height=100,
            placeholder="Type your question here...",
            help=query_help_text
        )
        
        if st.button("Submit Question", help="Get an answer based on the graph's knowledge"):
            if query:
                with st.spinner("Processing your question..."):
                    result = self.query_engine.process_query(query)
                    st.session_state.query_result = result # Store result for potential reuse
                    
                    # --- Generate and Display LLM Answer --- 
                    st.subheader("Answer")
                    # Format the evidence for the LLM prompt
                    evidence_summary = self._format_evidence_for_llm(result.evidence)
                    # Simulate LLM call
                    llm_answer = self._generate_llm_answer(query, evidence_summary)
                    st.markdown(llm_answer) # Display the generated answer

                    # Display confidence separately
                    st.metric("Overall Confidence", f"{result.confidence:.2f}", 
                              help="How sure the system is about the relevance of the found information to your query (before LLM generation)")
                    st.markdown("---")
                    
                    # --- Display Evidence (Raw) --- 
                    with st.expander("Supporting Evidence (Raw Data)"):
                        if result.evidence:
                            for item in result.evidence:
                                st.json(item)
                        else:
                            st.write("No specific evidence identified.")
                            
                    # --- Display Explanation --- 
                    with st.expander("Explanation (Insights)"):
                        try:
                            explanation = self.explainer.explain_query_result(result)
                            self._display_explanation(explanation)
                        except Exception as e:
                            logger.error(f"Error generating explanation: {e}", exc_info=True)
                            st.error(f"Could not generate explanation: {e}")
            else:
                st.warning("Please enter a question.")

        st.markdown("---")
        st.markdown("""
            <div class="info-box">
                <h4>💡 Query Tips</h4>
                <ul>
                    <li>Be specific if possible (e.g., use full names).</li>
                    <li>Try different phrasings if the first attempt doesn't work.</li>
                    <li>Use quotes around exact phrases if needed (e.g., "Project Phoenix").</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    def _show_entity_explorer(self):
        """Show the entity explorer interface."""
        st.header("Explore Items")
        st.caption("Browse and view details about specific items (entities) in the knowledge graph.")

        if not self.knowledge_store.entity_index:
            st.warning("Knowledge graph is empty. Add data via PDF or other methods.")
            return

        # Select entity
        entity_list = sorted(list(self.knowledge_store.entity_index.keys()))
        selected_entity_id = st.selectbox(
            "Select an item (entity) to explore:", 
            entity_list,
            index=0, # Default to first item
            help="Choose an item from the graph to see its details and connections."
        )
        
        if selected_entity_id:
            entity = self.knowledge_store.get_entity(selected_entity_id)
            if entity:
                st.subheader(f"Details for: {selected_entity_id} ({entity.type})")
                
                # Tabs for different views
                tab1, tab2, tab3 = st.tabs(["Properties", "Connections", "Analysis"])
                
                with tab1:
                    st.write("**Properties:**")
                    if entity.properties:
                        # Display properties in a more readable way
                        prop_data = {k: str(v) for k,v in entity.properties.items()} # Ensure values are strings for display
                        st.table(prop_data)
                    else:
                        st.info("No properties defined for this item.")
                
                with tab2:
                    st.write("**Connections (Relationships):**")
                    relationships = self.knowledge_store.get_relationships(selected_entity_id)
                    if relationships:
                         for rel in relationships:
                             # Display relationships more readably
                             source_disp = f"**{rel.source}**" if rel.source == selected_entity_id else rel.source
                             target_disp = f"**{rel.target}**" if rel.target == selected_entity_id else rel.target
                             st.markdown(f"- {source_disp} --- `{rel.type}` ---> {target_disp}")
                             if rel.properties:
                                 st.markdown(f"  - Properties: `{rel.properties}`")
                    else:
                        st.info("No connections found for this item.")
                
                with tab3:
                    st.write("**Analysis:**")
                    with st.spinner("Analyzing item..."):
                        try:
                            explanation = self.explainer.explain_entity(selected_entity_id)
                            self._display_entity_explanation(explanation)
                        except Exception as e:
                            logger.error(f"Error generating entity explanation for {selected_entity_id}: {e}", exc_info=True)
                            st.error(f"Could not analyze item: {e}")
            else:
                st.error(f"Could not retrieve details for entity ID: {selected_entity_id}")
    
    def _show_xai_dashboard(self):
        """Show the XAI dashboard interface."""
        st.header("Graph Insights (XAI Dashboard)")
        st.caption("Explore overall graph characteristics and understand item importance.")

        if not self.knowledge_store.graph or self.knowledge_store.graph.number_of_nodes() == 0:
            st.warning("Knowledge graph is empty or has no nodes. Add data first.")
            return
        
        tab1, tab2, tab3 = st.tabs(["Saliency Analysis", "Feature Importance", "Counterfactuals (Placeholder)"])

        with tab1:
            self._show_saliency_analysis()
        
        with tab2:
            self._show_feature_importance()
        
        with tab3:
            self._show_counterfactual_analysis()
    
    def _show_saliency_analysis(self):
        """Display saliency analysis options and results."""
        st.subheader("Item Influence Analysis (Saliency)")
        st.markdown("Analyze the importance or influence of specific items within the graph structure.")

        entity_list = sorted(list(self.knowledge_store.entity_index.keys()))
        if not entity_list:
             st.info("No items available to analyze.")
             return
            
        selected_entity = st.selectbox(
            "Select item to analyze its influence:", 
            entity_list,
            key="saliency_entity_select",
            help="Choose an item to see its centrality scores and community role."
        )

        if st.button("Analyze Influence", key="analyze_saliency_button"):
            if selected_entity:
                with st.spinner(f"Analyzing influence of {selected_entity}..."):
                    try:
                        # Correct the call: remove empty string, use keyword arg, pass as list
                        analysis = self.saliency_analyzer.analyze(target_nodes=[selected_entity])
                        
                        # Display results 
                        st.write("#### Analysis Results")
                        # Use correct structure from analyze method
                        centrality_scores = analysis.get("centrality_scores", {}).get(selected_entity, {})
                        if centrality_scores:
                             st.write("**Connectedness Scores:**")
                             st.markdown(self._format_scores(centrality_scores), unsafe_allow_html=True)
                        else:
                             st.info("No centrality scores available.")
                    except Exception as e:
                         logger.error(f"Saliency analysis failed for {selected_entity} in UI: {e}", exc_info=True)
                         st.error(f"Analysis failed: {e}")
            else:
                 st.warning("Please select an item to analyze.")
                
    def _show_feature_importance(self):
        """Display feature importance analysis results."""
        st.subheader("Key Characteristics (Feature Importance)")
        st.markdown("Analyze which general features (like types or properties) are most characteristic or important in the graph.")

        if st.button("Analyze Graph Features", key="analyze_features_button"):
            with st.spinner("Analyzing graph features..."):
                try:
                    analysis = self.explainer.feature_analyzer.analyze() # Analyze whole graph
                    
                    st.write("#### Feature Category Importance")
                    importance_scores = analysis.get('importance_scores', {})
                    if importance_scores:
                         st.markdown(self._format_scores(importance_scores), unsafe_allow_html=True)
                    else:
                         st.info("No category importance scores calculated.")
                    
                    st.write("#### Top Specific Features (e.g., Properties)")
                    ranked_features = analysis.get('ranked_features', [])
                    if ranked_features:
                        for feature, score in ranked_features:
                             st.markdown(f"- `{feature}` : {score:.4f}")
                    else:
                        st.info("No specific features ranked.")
                except Exception as e:
                     logger.error(f"Feature importance analysis failed in UI: {e}", exc_info=True)
                     st.error(f"Analysis failed: {e}")
    
    def _show_counterfactual_analysis(self):
        """Display counterfactual analysis options and results (Placeholder)."""
        st.subheader("What-If Scenarios (Counterfactuals)")
        st.warning("This section is a placeholder for future implementation.")
        st.markdown("Counterfactual analysis helps understand how small changes to the graph might affect query results.")
        # Placeholder for inputs needed for counterfactuals
        # original_query = st.text_input("Original Query:")
        # target_outcome = st.text_input("Desired Outcome:")
        # if st.button("Suggest Changes"):
        #     if original_query and target_outcome:
        #         suggestions = self.explainer.suggest_counterfactuals(...
        #         st.write(suggestions)
    
    def _show_pdf_upload_page(self):
        """Renders the page for uploading and processing PDF files."""
        st.header("Add Data from PDF")
        st.caption("Upload a PDF document. The system will attempt to extract text, identify key items (entities) and their connections (relationships), and add them to the main knowledge graph.")

        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf", 
            help="Select a PDF file from your computer to process."
        )

        if uploaded_file is not None:
            st.write(f"File selected: `{uploaded_file.name}`")
            
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            # Use a temporary file context manager if possible, otherwise manual cleanup
            temp_file_path = os.path.join(temp_dir, uploaded_file.name) 
            parse_button_pressed = st.button("Process PDF", key="parse_pdf_button", help="Extract knowledge from the uploaded PDF and add it to the graph.")
            
            if parse_button_pressed:
                try:
                    # Save the uploaded file temporarily
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    logger.info(f"Saved uploaded file temporarily to: {temp_file_path}")

                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        logger.info(f"UI: Initiating PDF parsing for {uploaded_file.name}")
                        st.session_state.pdf_processing_log = [] # Clear previous logs
                        parsed_store = self.pdf_parser.parse_pdf(temp_file_path)
                        # st.session_state.query_result = None # Clear query results (already done in query page logic)

                        if parsed_store:
                            entity_count = len(parsed_store.entity_index)
                            rel_count = len(parsed_store.relationship_index)
                            log_entry = f"Successfully parsed '{uploaded_file.name}'. Found {entity_count} items, {rel_count} connections."
                            st.session_state.pdf_processing_log.append(log_entry)
                            st.success(log_entry)
                            logger.info(log_entry)
                            
                            # Merge into main store
                            # Note: This simple update might overwrite existing entities/relationships 
                            # with the same ID/key if the PDF parser generates overlapping IDs. 
                            # A more robust merge strategy might be needed for production.
                            self.knowledge_store.graph.update(parsed_store.graph)
                            self.knowledge_store.entity_index.update(parsed_store.entity_index)
                            self.knowledge_store.relationship_index.update(parsed_store.relationship_index)
                            # st.session_state.uploaded_pdf_store = parsed_store # Maybe not needed if merged
                            logger.info("Merged parsed PDF knowledge into main store.")
                            st.info("Knowledge from PDF merged into the main graph.")
                            
                            # Re-initialize explainer to use updated graph state
                            logger.info("Re-initializing graph explainer with updated knowledge store...")
                            self.explainer = GraphExplainer(self.knowledge_store)
                            logger.info("Graph explainer re-initialized.")
                            st.rerun() # Rerun the script to reflect changes immediately
                            
                        else:
                            log_entry = f"Failed to parse '{uploaded_file.name}' or no data extracted. Check logs."
                            st.session_state.pdf_processing_log.append(log_entry)
                            st.error(log_entry)
                            logger.error(log_entry)
                            # st.session_state.uploaded_pdf_store = None
                            
                except Exception as e:
                    st.error(f"An error occurred during file handling or parsing: {e}")
                    logger.error(f"Error during PDF upload/parse process: {e}", exc_info=True)
                    # st.session_state.uploaded_pdf_store = None
                finally:
                     # Clean up temp file
                     if os.path.exists(temp_file_path):
                         try:
                             os.remove(temp_file_path)
                             logger.info(f"Removed temporary file: {temp_file_path}")
                         except Exception as e_clean:
                             logger.warning(f"Could not remove temporary file {temp_file_path}: {e_clean}")

        # Display processing logs (consider moving below button?)
        if st.session_state.pdf_processing_log:
            st.subheader("Last PDF Processing Log")
            for log in st.session_state.pdf_processing_log:
                st.text(log)
    
    def _display_explanation(self, explanation: Dict[str, Any]):
        """Helper function to display the explanation dictionary structure nicely."""
        if not explanation:
            st.write("No explanation data available.")
            return

        st.subheader("Analysis Breakdown")
        # Saliency
        st.markdown("**Item Influence (Saliency):**")
        saliency = explanation.get('saliency', {})
        if saliency.get("error"):
             st.error(f"Saliency analysis failed: {saliency['error']}")
        elif saliency:
            centrality_scores = saliency.get('centrality_scores')
            if centrality_scores:
                 st.markdown("Connectedness Scores:")
                 st.json(self._format_scores(centrality_scores), expanded=False) # Keep collapsed initially
        else:
            st.write("No saliency data.")
        st.markdown("---")

        # Feature Importance
        st.markdown("**Key Characteristics (Feature Importance):**")
        feature_importance = explanation.get('feature_importance', {})
        if feature_importance.get("error"):
             st.error(f"Feature importance analysis failed: {feature_importance['error']}")
        elif feature_importance:
            importance_scores = feature_importance.get('importance_scores')
            if importance_scores:
                 st.markdown("Category Importance:")
                 st.json(self._format_scores(importance_scores), expanded=False)
            ranked_features = feature_importance.get('ranked_features', [])
            if ranked_features:
                 st.markdown("Top Specific Features:")
                 # Format ranked features list nicely
                 feature_str = ", ".join([f"`{f}` ({s:.2f})" for f, s in ranked_features])
                 st.markdown(f"- {feature_str}")
        else:
            st.write("No feature importance data.")
        st.markdown("---")
    
    def _display_entity_explanation(self, explanation: Dict[str, Any]):
        """Display entity explanation details correctly parsing the structure.
        
        Args:
            explanation: The dictionary returned by GraphExplainer.explain_entity.
        """
        if not explanation or explanation.get("error"):
            st.warning(f"Could not generate full explanation: {explanation.get('error', 'Unknown error')}")
            return

        # --- Display Saliency --- 
        st.write("**Item Influence (Saliency Analysis)**")
        saliency_data = explanation.get('saliency', {})
        if saliency_data.get("error"):
            st.error(f"Saliency analysis failed: {saliency_data['error']}")
        elif saliency_data:
            st.write("Connectedness Scores:")
            centrality_scores = saliency_data.get("centrality_scores", {})
            # Centrality scores are nested one level deeper (entity_id -> scores)
            for entity_id, scores in centrality_scores.items(): # Should only be one entity_id here
                if scores: 
                    # Use internal _format_scores for nice HTML table
                    st.markdown(self._format_scores_as_html_table(scores), unsafe_allow_html=True)
                else:
                     st.markdown("N/A")
        else:
            st.info("No saliency data available.")

        st.markdown("---")

        # --- Display Feature Importance --- 
        st.write("**Key Characteristics (Feature Importance)**")
        feature_data = explanation.get('feature_importance', {})
        if feature_data.get("error"):
             st.error(f"Feature importance analysis failed: {feature_data['error']}")
        elif feature_data:
            st.write("Category Importance:")
            importance_scores = feature_data.get('importance_scores', {})
            if importance_scores:
                 st.markdown(self._format_scores_as_html_table(importance_scores), unsafe_allow_html=True)
            else:
                 st.info("No importance scores calculated.")
        else:
             st.info("No feature importance data available.")
    
    def _format_scores_as_html_table(self, scores: Dict[str, float]) -> str:
        """Formats a simple score dictionary as a small HTML table."""
        if not scores: return ""
        rows = "".join([f"<tr><td>{k.replace('_', ' ').title()}</td><td>{v:.3f}</td></tr>" 
                       for k, v in scores.items() if isinstance(v, (float, int))])
        return f"<table style='width: auto; font-size: 0.9em;'>{rows}</table>"

    def _format_scores(self, data: Dict) -> Dict:
        """Recursively formats numerical scores in a nested dictionary to 2 decimal places.
           Used primarily for st.json output.
        """ 
        formatted = {}
        for key, value in data.items():
            if isinstance(value, dict):
                formatted[key] = self._format_scores(value) # Use self now
            elif isinstance(value, (float, np.float32, np.float64)):
                try:
                    formatted[key] = f"{value:.2f}" # Format floats
                except (TypeError, ValueError):
                    formatted[key] = str(value) # Fallback for non-format-able numbers
            else:
                formatted[key] = value # Keep other types as is
        return formatted

    def _format_evidence_for_llm(self, evidence: List[Dict[str, Any]], max_items: int = 5) -> str:
        """Formats the evidence list into a string summary for an LLM prompt."""
        if not evidence:
            return "No specific relevant information found in the graph."
        
        summary_lines = ["Relevant information found in the knowledge graph:"]
        
        entities_found = [item for item in evidence if item.get('type') == 'entity']
        relationships_found = [item for item in evidence if item.get('type') == 'relationship']
        
        if entities_found:
            summary_lines.append("\nKey Items (Entities):")
            for entity_evidence in entities_found[:max_items]:
                entity_id = entity_evidence.get('id', '[Unknown ID]')
                entity_type = entity_evidence.get('entity_type', 'Unknown')
                props = entity_evidence.get('properties', {})
                # Use 'text' property as the primary name, fall back to ID if 'text' is missing
                display_name = props.get('text', entity_id) 
                # Optional: Include other key properties if desired, but keep it concise for LLM
                # display_props_str = ", ".join([f'{k}: {v}' for k,v in props.items() if k != 'text']) # Example
                summary_lines.append(f"- Item: '{display_name}' (Type: {entity_type})") # Emphasize display_name
                # Optionally add ID back if needed for disambiguation, but maybe not necessary for LLM context
                # summary_lines.append(f"- Item: '{display_name}' (Type: {entity_type}, ID: `{entity_id}`)")
        
        if relationships_found:
            summary_lines.append("\nRelevant Connections (Relationships):")
            for rel_evidence in relationships_found[:max_items]:
                rel_type = rel_evidence.get('relationship_type', 'related')
                source = rel_evidence.get('source', '?')
                target = rel_evidence.get('target', '?')
                summary_lines.append(f"- Connection: `{source}` --[{rel_type}]--> `{target}`")
                
        return "\n".join(summary_lines)

    def _generate_llm_answer(self, query: str, evidence_summary: str) -> str:
        """Simulates generating an answer using an LLM with provided context."""
        logger.info("Generating LLM answer via Ollama (Phi-3)...")

        model_name = "phi3" # <--- Use the phi3 model

        # Simple prompt structure (you might need to refine this based on Phi-3's behavior)
        prompt = f"""<|user|>
Based on the user's question and the provided context from a knowledge graph, generate a helpful, concise answer.

User Question: {query}

Knowledge Graph Context:
{evidence_summary}
<|end|>
<|assistant|>""" # Using the standard Phi-3 chat prompt format

        ollama_endpoint = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False, # Get the full response at once
            "options": { # Optional: Adjust parameters if needed
                "temperature": 0.7 
            }
        }

        try:
            # Increase timeout as CPU inference can be slower
            response = requests.post(ollama_endpoint, json=payload, timeout=120) 
            response.raise_for_status() # Raise error for bad status codes

            response_data = response.json()
            # Ensure 'response' key exists before accessing
            if 'response' in response_data:
                # Strip potential leading/trailing whitespace or markers
                return response_data['response'].strip() 
            else:
                logger.error(f"Ollama response missing 'response' key: {response_data}")
                return "(Error: Could not parse LLM response)"

        except requests.exceptions.Timeout:
             logger.error(f"Timeout calling Ollama API after 120 seconds.")
             return "(Error: LLM generation timed out - the model might be taking too long on CPU)"
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            # Check if Ollama is running
            return f"(Error: Could not connect to local LLM - is Ollama running? Details: {e})"
        except json.JSONDecodeError as e:
                logger.error(f"Error decoding Ollama JSON response: {e}")
                return "(Error: Invalid response format from LLM)"
        except Exception as e:
                logger.error(f"Unexpected error during LLM generation: {e}", exc_info=True)
                return "(Error: An unexpected error occurred during generation)"

# --- App Entry Point --- 

@st.cache_resource
def load_core_components():
    """Loads or initializes the core CognisGraph components (cached)."""
    logger.info("Loading core CognisGraph components...")
    store = KnowledgeStore()
    engine = QueryEngine(store)
    # Add some initial data for demonstration 
    try:
        store.add_entity(Entity(id="Python", type="Language", properties={"creator": "Guido"}))
        store.add_entity(Entity(id="Streamlit", type="Framework", properties={"language": "Python"}))
        store.add_relationship(Relationship(source="Streamlit", target="Python", type="uses", properties={}))
    except Exception as e:
        logger.error(f"Failed to add initial demo data: {e}")
    logger.info("Core components loaded.")
    return store, engine

if __name__ == "__main__":
    # Load components
    knowledge_store, query_engine = load_core_components()
    
    # Create and run UI
    ui = CognisGraphUI(knowledge_store, query_engine)
    ui.run() 