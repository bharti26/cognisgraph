import streamlit as st
import os
import asyncio
from cognisgraph import CognisGraph
from cognisgraph.config import Config
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temp directory for uploaded files
TEMP_UPLOAD_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

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
            return {"status": "success", "data": result.get("data", {})}
        else:
            return {"status": "error", "message": result.get("message", "Error generating visualization")}
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return {"status": "error", "message": str(e)}

def main():
    st.title("CognisGraph")
    
    # Initialize CognisGraph
    cognisgraph = init_cognisgraph()
    
    # File upload section
    st.header("Upload and Process PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name
        
        # Process the PDF
        if st.button("Process PDF"):
            with st.spinner("Processing PDF..."):
                result = asyncio.run(process_pdf(cognisgraph, tmp_path))
                
                if result["status"] == "success":
                    st.success("PDF processed successfully!")
                    
                    # Display entities in an expandable section
                    if "entities" in result.get("data", {}):
                        with st.expander("Extracted Entities", expanded=False):
                            for entity in result["data"]["entities"]:
                                st.write(f"**{entity['id']}** ({entity['type']})")
                                if entity.get("properties"):
                                    st.json(entity["properties"])
                    
                    # Display relationships in an expandable section
                    if "relationships" in result.get("data", {}):
                        with st.expander("Extracted Relationships", expanded=False):
                            for rel in result["data"]["relationships"]:
                                st.write(f"**{rel['source']} → {rel['target']}** ({rel['type']})")
                                if rel.get("properties"):
                                    st.json(rel["properties"])
                    
                    # Generate and display visualization
                    with st.spinner("Generating visualization..."):
                        viz_result = asyncio.run(generate_visualization(cognisgraph))
                        if viz_result["status"] == "success":
                            # Display the Plotly figure
                            st.plotly_chart(viz_result["data"]["figure"])
                            
                            # Display graph metrics in an expandable section
                            with st.expander("Graph Metrics", expanded=False):
                                metrics = viz_result["data"]["graph_info"]
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("Nodes", metrics["num_nodes"])
                                    st.metric("Edges", metrics["num_edges"])
                                    st.metric("Density", f"{metrics['density']:.3f}")
                                
                                with col2:
                                    st.metric("Average Degree", f"{metrics['average_degree']:.2f}")
                                    st.metric("Components", metrics["components"])
                                    st.metric("Connected", "Yes" if metrics["is_connected"] else "No")
                            
                            # Display explanation if available
                            if "explanation" in viz_result:
                                with st.expander("Graph Analysis", expanded=False):
                                    st.markdown(viz_result["explanation"])
                        else:
                            st.error(f"Error generating visualization: {viz_result.get('message', 'Unknown error')}")
                else:
                    st.error(f"Error processing PDF: {result.get('message', 'Unknown error')}")
            
            # Clean up temporary file
            os.unlink(tmp_path)
    
    # Query section
    st.header("Query Knowledge Graph")
    query = st.text_input("Enter your query:")
    
    if query and st.button("Search"):
        with st.spinner("Processing query..."):
            result = asyncio.run(process_query(cognisgraph, query))
            
            if result["status"] == "success":
                st.success("Query processed successfully!")
                
                # Display answer in a nice format
                answer_data = result["data"]
                st.markdown(f"### Answer\n{answer_data['answer']}")
                
                # Show confidence if available
                if answer_data.get("confidence"):
                    st.progress(float(answer_data["confidence"]))
                    st.caption(f"Confidence: {answer_data['confidence']:.2%}")
                
                # Show explanation if available
                if answer_data.get("explanation"):
                    with st.expander("Explanation", expanded=False):
                        st.markdown(answer_data["explanation"])
            else:
                st.error(f"Error processing query: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main() 