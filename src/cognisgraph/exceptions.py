class CognisGraphError(Exception):
    """Base exception for CognisGraph errors."""
    pass

class KnowledgeError(CognisGraphError):
    """Exception raised for errors in knowledge operations."""
    pass

class QueryError(CognisGraphError):
    """Exception raised for errors in query operations."""
    pass

class VisualizationError(CognisGraphError):
    """Exception raised for errors in visualization operations."""
    pass

class WorkflowError(CognisGraphError):
    """Exception raised for errors in workflow operations."""
    pass

class ConfigurationError(CognisGraphError):
    """Exception raised for errors in configuration."""
    pass

class EntityNotFoundError(KnowledgeError):
    """Exception raised when an entity is not found in the knowledge graph."""
    pass

class RelationshipError(KnowledgeError):
    """Exception raised for errors in relationship operations."""
    pass

class InvalidQueryError(QueryError):
    """Exception raised for invalid queries."""
    pass

class VisualizationMethodError(VisualizationError):
    """Exception raised for invalid visualization methods."""
    pass

class WorkflowExecutionError(WorkflowError):
    """Exception raised for errors during workflow execution."""
    pass 