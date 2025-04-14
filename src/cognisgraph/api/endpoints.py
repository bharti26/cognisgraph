from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.query_engine import QueryEngine
from cognisgraph.agents.orchestrator import OrchestratorAgent
from cognisgraph.agents.pdf_agent import PDFProcessingAgent
from cognisgraph.visualization.graph_visualizer import GraphVisualizer
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship
from langchain_community.llms import Ollama
import networkx as nx
import json
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

# Models for request validation
class QueryRequest(BaseModel):
    query: str = Field(..., description="The query to process")

class EntityData(BaseModel):
    id: str = Field(..., description="Entity ID")
    type: str = Field(..., description="Entity type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")

class RelationshipData(BaseModel):
    source: str = Field(..., description="Source entity ID")
    target: str = Field(..., description="Target entity ID")
    type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")

app = FastAPI(title="CognisGraph API", description="API for interacting with the CognisGraph knowledge graph system")

# Initialize components
knowledge_store = KnowledgeStore()
llm = Ollama(model="llama2")
query_engine = QueryEngine(knowledge_store)
pdf_agent = PDFProcessingAgent(knowledge_store=knowledge_store, llm=llm)
orchestrator = OrchestratorAgent(knowledge_store, query_engine, pdf_agent=pdf_agent)

# Valid visualization methods
VALID_VISUALIZATION_METHODS = ["plotly", "networkx", "pyvis", "graphviz"]

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and process a PDF file."""
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Process the PDF
        result = pdf_agent.process(temp_file_path)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return {
            "status": "success",
            "message": "PDF processed successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """Process a natural language query."""
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        result = await orchestrator.process(request.query)
        return {
            "status": "success",
            "result": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualize")
async def visualize_graph(method: str = "plotly") -> Dict[str, Any]:
    """Generate a visualization of the knowledge graph."""
    if method not in VALID_VISUALIZATION_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid visualization method. Must be one of: {', '.join(VALID_VISUALIZATION_METHODS)}")
        
    try:
        # Get the current graph
        graph = knowledge_store.get_graph()
        visualizer = GraphVisualizer(graph)
        
        # Create a temporary file for the visualization
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html" if method in ["plotly", "pyvis"] else ".png") as temp_file:
            output_path = temp_file.name
            
        # Generate the visualization
        if method == "plotly":
            fig = visualizer.plot_plotly(output_path=output_path)
            return {
                "status": "success",
                "visualization_path": output_path,
                "type": "plotly"
            }
        elif method == "networkx":
            visualizer.plot_networkx(output_path=output_path)
            return {
                "status": "success",
                "visualization_path": output_path,
                "type": "networkx"
            }
        elif method == "pyvis":
            visualizer.plot_pyvis(output_path=output_path)
            return {
                "status": "success",
                "visualization_path": output_path,
                "type": "pyvis"
            }
        elif method == "graphviz":
            visualizer.plot_graphviz(output_path=output_path)
            return {
                "status": "success",
                "visualization_path": f"{output_path}.png",
                "type": "graphviz"
            }
    except Exception as e:
        # Clean up temporary file if it exists
        if 'output_path' in locals():
            try:
                os.unlink(output_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities")
async def get_entities() -> List[Dict[str, Any]]:
    """Get all entities in the knowledge graph."""
    try:
        entities = knowledge_store.get_entities()
        return [{"id": e.id, "type": e.type, "properties": e.properties} for e in entities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/relationships")
async def get_relationships() -> List[Dict[str, Any]]:
    """Get all relationships in the knowledge graph."""
    try:
        relationships = []
        for entity in knowledge_store.get_entities():
            entity_rels = knowledge_store.get_relationships(entity.id)
            relationships.extend([{
                "source": rel.source,
                "target": rel.target,
                "type": rel.type,
                "properties": rel.properties
            } for rel in entity_rels])
        return relationships
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/entity")
async def add_entity(entity_data: EntityData) -> Dict[str, Any]:
    """Add a new entity to the knowledge graph."""
    try:
        entity = Entity(
            id=entity_data.id,
            type=entity_data.type,
            properties=entity_data.properties
        )
        knowledge_store.add_entity(entity)
        return {
            "status": "success",
            "message": "Entity added successfully",
            "entity": {
                "id": entity.id,
                "type": entity.type,
                "properties": entity.properties
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/relationship")
async def add_relationship(relationship_data: RelationshipData) -> Dict[str, Any]:
    """Add a new relationship to the knowledge graph."""
    try:
        # Check if source and target entities exist
        if not knowledge_store.get_entity(relationship_data.source):
            raise HTTPException(status_code=400, detail=f"Source entity {relationship_data.source} not found")
        if not knowledge_store.get_entity(relationship_data.target):
            raise HTTPException(status_code=400, detail=f"Target entity {relationship_data.target} not found")
            
        relationship = Relationship(
            source=relationship_data.source,
            target=relationship_data.target,
            type=relationship_data.type,
            properties=relationship_data.properties
        )
        knowledge_store.add_relationship(relationship)
        return {
            "status": "success",
            "message": "Relationship added successfully",
            "relationship": {
                "source": relationship.source,
                "target": relationship.target,
                "type": relationship.type,
                "properties": relationship.properties
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 