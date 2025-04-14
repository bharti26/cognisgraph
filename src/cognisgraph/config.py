from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

class VisualizationConfig(BaseModel):
    """Configuration for visualization settings."""
    default_method: str = Field(default="plotly", description="Default visualization method")
    plotly_config: Dict[str, Any] = Field(
        default={
            "layout": "spring",
            "node_size": 10,
            "edge_width": 1
        },
        description="Plotly-specific configuration"
    )
    networkx_config: Dict[str, Any] = Field(
        default={
            "layout": "spring",
            "node_color": "lightblue",
            "node_size": 500
        },
        description="NetworkX-specific configuration"
    )

class WorkflowConfig(BaseModel):
    """Configuration for workflow settings."""
    enable_visualization: bool = Field(default=True, description="Whether to enable visualization in workflows")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed operations")
    timeout: int = Field(default=30, description="Timeout in seconds for workflow operations")

class CognisGraphConfig(BaseModel):
    """Main configuration for CognisGraph."""
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    debug: bool = Field(default=False, description="Enable debug mode")
    
    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> 'CognisGraphConfig':
        """Create a configuration from a dictionary."""
        if config_dict is None:
            return cls()
        return cls(**config_dict)

@dataclass
class Config:
    """Configuration class for CognisGraph."""
    
    log_level: str = "INFO"
    log_file: Optional[str] = None
    debug: bool = False
    
    @classmethod
    def from_dict(cls, config: Optional[Dict[str, Any]] = None) -> 'Config':
        """Create a Config instance from a dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Config instance
        """
        if config is None:
            return cls()
        
        return cls(
            log_level=config.get("log_level", "INFO"),
            log_file=config.get("log_file"),
            debug=config.get("debug", False)
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return getattr(self, key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary access.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value
        """
        return getattr(self, key) 