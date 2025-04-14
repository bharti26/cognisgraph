from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Union
import json
from ..core.graph import CognisGraph
from ..core.visualization import GraphVisualizer, NodeStyle, EdgeStyle
from ..core.metrics import PerformanceTracker
import tempfile
import os

app = FastAPI(title="CognisGraph API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
cognis = CognisGraph()
visualizer = GraphVisualizer()
metrics = PerformanceTracker()

class NodeStyleRequest(BaseModel):
    size: Optional[int] = None
    color: Optional[str] = None
    symbol: Optional[str] = None
    opacity: Optional[float] = None
    line_width: Optional[int] = None
    line_color: Optional[str] = None
    text_font_size: Optional[int] = None
    text_font_color: Optional[str] = None
    hover_text: Optional[str] = None
    hover_template: Optional[str] = None
    custom_data: Optional[Dict] = None

class EdgeStyleRequest(BaseModel):
    width: Optional[float] = None
    color: Optional[str] = None
    opacity: Optional[float] = None
    dash: Optional[str] = None
    arrow_size: Optional[float] = None
    hover_text: Optional[str] = None
    hover_template: Optional[str] = None
    custom_data: Optional[Dict] = None

class VisualizationRequest(BaseModel):
    layout: Optional[str] = "force-directed"
    title: Optional[str] = "Knowledge Graph"
    show_metrics: Optional[bool] = True
    node_attributes: Optional[Dict[str, str]] = None
    edge_attributes: Optional[Dict[str, str]] = None
    node_styles: Optional[Dict[str, NodeStyleRequest]] = None
    edge_styles: Optional[Dict[str, EdgeStyleRequest]] = None

@app.post("/api/visualization/set_node_style")
async def set_node_style(node_type: str, style: NodeStyleRequest):
    """Set custom style for a specific node type."""
    try:
        node_style = NodeStyle(
            size=style.size or 20,
            color=style.color or "#1f77b4",
            symbol=style.symbol or "circle",
            opacity=style.opacity or 1.0,
            line_width=style.line_width or 2,
            line_color=style.line_color or "#000000",
            text_font_size=style.text_font_size or 12,
            text_font_color=style.text_font_color or "#000000",
            hover_text=style.hover_text,
            hover_template=style.hover_template,
            custom_data=style.custom_data
        )
        visualizer.set_node_style(node_type, node_style)
        return {"message": f"Node style set for type: {node_type}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/visualization/set_edge_style")
async def set_edge_style(edge_type: str, style: EdgeStyleRequest):
    """Set custom style for a specific edge type."""
    try:
        edge_style = EdgeStyle(
            width=style.width or 2.0,
            color=style.color or "#888888",
            opacity=style.opacity or 0.8,
            dash=style.dash or "solid",
            arrow_size=style.arrow_size or 0.5,
            hover_text=style.hover_text,
            hover_template=style.hover_template,
            custom_data=style.custom_data
        )
        visualizer.set_edge_style(edge_type, edge_style)
        return {"message": f"Edge style set for type: {edge_type}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/visualization/generate")
async def generate_visualization(request: VisualizationRequest):
    """Generate a visualization with custom styles and metrics."""
    try:
        # Apply custom styles if provided
        if request.node_styles:
            for node_type, style in request.node_styles.items():
                await set_node_style(node_type, style)
        
        if request.edge_styles:
            for edge_type, style in request.edge_styles.items():
                await set_edge_style(edge_type, style)

        # Generate visualization
        fig = visualizer.visualize_graph(
            cognis.graph,
            layout=request.layout,
            title=request.title,
            show_metrics=request.show_metrics,
            node_attributes=request.node_attributes,
            edge_attributes=request.edge_attributes
        )

        # Convert to JSON
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Get a summary of all performance metrics."""
    try:
        return metrics.get_metrics_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/operation/{operation_name}")
async def get_operation_metrics(operation_name: str):
    """Get metrics for a specific operation type."""
    try:
        return {
            "average_duration": metrics.get_average_duration(operation_name),
            "success_rate": metrics.get_success_rate(operation_name)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... existing endpoints ... 