from typing import Dict, Any, Optional, List, Union
from .core.knowledge_store import KnowledgeStore, Entity, Relationship
from .core.query_engine import QueryEngine, QueryResult
from .core.langgraph_workflow import CognisGraphWorkflow
from .visualization.graph_visualizer import GraphVisualizer
from .config import CognisGraphConfig
from .utils.logger import CognisGraphLogger
from .exceptions import (
    CognisGraphError, KnowledgeError, QueryError,
    VisualizationError, WorkflowError
)
from .parsers.pdf_parser import PDFParser
from .xai.explainer import GraphExplainer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CognisGraph:
    """Main class for interacting with the CognisGraph knowledge graph system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CognisGraph with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            # Initialize configuration
            self.config = CognisGraphConfig.from_dict(config)
            
            # Initialize logger
            self.logger = CognisGraphLogger(
                log_file="logs/cognisgraph.log" if self.config.debug else None
            )
            
            # Initialize components
            self.knowledge_store = KnowledgeStore()
            self.query_engine = QueryEngine(self.knowledge_store)
            self.workflow = CognisGraphWorkflow(self.knowledge_store, self.query_engine)
            self.visualizer = GraphVisualizer(self.knowledge_store.graph)
            self.pdf_parser = PDFParser() # Initialize parser
            self.explainer = GraphExplainer(self.knowledge_store) # Initialize explainer
            
            self.logger.info("CognisGraph initialized successfully")
        except Exception as e:
            self.logger.critical(f"Failed to initialize CognisGraph: {str(e)}")
            raise
    
    def add_knowledge(
        self,
        knowledge: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """
        Add knowledge to the graph. Can be a single item or a list of items.
        Each item should minimally have an 'entity' key.
        Optionally includes 'type', 'properties', and 'relationships'.
    
        Args:
            knowledge: Knowledge dict or list of dicts to add.
    
        Returns:
            bool: True if all knowledge was processed successfully (relationships might
                  still fail silently if target entities don't exist), False otherwise.
    
        Raises:
            KnowledgeError: If there's a fundamental error processing the input.
        """
        try:
            if isinstance(knowledge, list):
                results = [self._add_single_knowledge(item) for item in knowledge]
                return all(results)
            return self._add_single_knowledge(knowledge)
        except KeyError as e:
            self.logger.error(f"Missing required key '{e}' in knowledge item: {knowledge}")
            raise KnowledgeError(f"Missing required key '{e}' in knowledge item.") from e
        except Exception as e:
            self.logger.error(f"Error adding knowledge: {str(e)}", exc_info=True)
            raise KnowledgeError(f"Failed to add knowledge: {str(e)}") from e

    def _add_single_knowledge(self, knowledge: Dict[str, Any]) -> bool:
        """Adds or updates a single knowledge item (entity and/or its relationships)."""
        entity_id = knowledge["entity"] # Required key
        added_entity_successfully = True
        processed_relationships = True

        # Check if entity exists or needs to be created/updated
        existing_entity = self.knowledge_store.get_entity(entity_id)
        
        if not existing_entity:
            # Entity doesn't exist, create it
            entity_type = knowledge.get('type', 'Unknown') # Default type if missing
            properties = knowledge.get('properties', {})   # Default properties if missing
            
            # Ensure 'text' property exists if possible
            if 'text' not in properties:
                 properties['text'] = entity_id # Use ID as text if not provided
                 
            try:
                entity = Entity(
                    id=entity_id,
                    type=entity_type,
                    properties=properties
                )
                added_entity_successfully = self.knowledge_store.add_entity(entity)
                if added_entity_successfully:
                     self.logger.info(f"Added new entity: '{entity_id}'")
                else:
                     # Logged within add_entity
                     pass
            except Exception as e:
                 self.logger.error(f"Failed to create/add entity '{entity_id}': {str(e)}")
                 added_entity_successfully = False
        else:
            # Entity exists - potentially update type/properties? (Not implemented yet)
            # For now, just log that it exists.
            self.logger.debug(f"Entity '{entity_id}' already exists. Processing relationships.")
            # TODO: Add logic to update existing entity properties/type if provided?
            pass 

        # Add relationships if provided and source entity exists/was added
        if added_entity_successfully and "relationships" in knowledge:
            if not isinstance(knowledge["relationships"], list):
                 self.logger.warning(f"'relationships' field for entity '{entity_id}' is not a list. Skipping.")
                 return added_entity_successfully # Return status of entity addition
                 
            rel_success_flags = []
            for rel_data in knowledge["relationships"]:
                if not isinstance(rel_data, dict) or 'target' not in rel_data or 'type' not in rel_data:
                    self.logger.warning(f"Skipping invalid relationship data for entity '{entity_id}': {rel_data}")
                    rel_success_flags.append(False)
                    continue
                    
                try:
                    relationship = Relationship(
                        source=entity_id, # Use the main entity ID as source
                        target=rel_data["target"],
                        type=rel_data["type"],
                        properties=rel_data.get("properties", {}) # Default props if missing
                    )
                    # add_relationship handles logging success/failure/missing target
                    rel_added = self.knowledge_store.add_relationship(relationship)
                    rel_success_flags.append(rel_added)
                except Exception as e:
                     self.logger.error(f"Error creating/adding relationship for '{entity_id}': {str(e)}")
                     rel_success_flags.append(False)
                     
            # We consider processing relationships successful if at least one was attempted,
            # even if some failed (e.g., due to missing targets, which is logged by store).
            # The overall success depends primarily on adding/finding the main entity.
            processed_relationships = bool(rel_success_flags)

        return added_entity_successfully # Return True if entity exists/was added
    
    def query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Query the knowledge graph.
        
        Args:
            query: The query string
            context: Optional context for the query
            
        Returns:
            QueryResult containing answer, confidence, and explanation
            
        Raises:
            QueryError: If there's an error processing the query
        """
        try:
            if not query or not isinstance(query, str):
                raise QueryError("Invalid query provided. Query must be a non-empty string.")
            result = self.query_engine.process_query(query, context)
            self.logger.info(f"Query processed successfully: {query}")
            return result
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            raise QueryError(f"Failed to process query: {str(e)}")
    
    def run_workflow(self, knowledge: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Run the LangGraph workflow with given knowledge and query.
        
        Args:
            knowledge: Knowledge to add to the graph
            query: Query to process
            
        Returns:
            Workflow state containing results
            
        Raises:
            WorkflowError: If there's an error running the workflow
        """
        try:
            if not query or not isinstance(query, str):
                raise WorkflowError("Invalid query provided for workflow. Query must be a non-empty string.")
            result = self.workflow.run(knowledge, query)
            self.logger.info("Workflow executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error running workflow: {str(e)}")
            raise WorkflowError(f"Failed to run workflow: {str(e)}")
    
    def visualize(
        self,
        method: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> None:
        """Generates a visualization of the knowledge graph.

        Args:
            method: Visualization method ("networkx", "plotly", "pyvis", or "graphviz")
            output_path: Optional path to save the visualization
            **kwargs: Additional arguments for the visualization method
            
        Raises:
            VisualizationError: If there's an error generating the visualization
        """
        logger.info(f"Generating graph visualization using method: {method}")
        try:
            # Use the self.visualizer instance initialized in __init__
            if method == "networkx":
                self.visualizer.plot_networkx(**kwargs)
            elif method == "plotly":
                fig = self.visualizer.plot_plotly(**kwargs)
                if output_path:
                    fig.write_html(output_path)
                else:
                    fig.show()
            elif method == "pyvis":
                self.visualizer.plot_pyvis(output_path or "knowledge_graph.html")
            elif method == "graphviz":
                self.visualizer.plot_graphviz(output_path or "knowledge_graph")
            else:
                # Check config for default if method is None or invalid?
                default_method = self.config.visualization.default_method
                logger.warning(f"Unknown or unspecified visualization method: '{method}'. Using default: '{default_method}'")
                # Attempt default (needs logic similar to above)
                if default_method == "networkx": self.visualizer.plot_networkx(**kwargs)
                elif default_method == "plotly": 
                     fig = self.visualizer.plot_plotly(**kwargs)
                     if output_path: fig.write_html(output_path)
                     else: fig.show()
                # Add other defaults as needed
                else: raise VisualizationError(f"Unknown default visualization method: {default_method}")

            logger.info(f"Visualization generated successfully using method: {method or default_method}")
        except Exception as e:
            logger.error(f"Error generating visualization with method '{method}': {e}", exc_info=True)
            raise VisualizationError(f"Failed to generate visualization: {str(e)}") from e
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self.knowledge_store.get_entity(entity_id)
    
    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        return self.knowledge_store.get_relationships(entity_id)
    
    def get_knowledge_graph(self):
        """Get the underlying networkx graph."""
        return self.knowledge_store.graph

    def parse_pdf(self, file_path: str) -> Optional[KnowledgeStore]:
        """Parses a PDF file and extracts entities/relationships into a KnowledgeStore.

        Args:
            file_path: The path to the PDF file.

        Returns:
            A KnowledgeStore containing the extracted knowledge, or None if parsing fails.
        """
        logger.info(f"Starting PDF parsing for: {file_path}")
        try:
            parsed_store = self.pdf_parser.parse_pdf(file_path)
            logger.info(f"Successfully parsed PDF: {file_path}. Found {len(parsed_store.entity_index)} entities and {len(parsed_store.relationship_index)} relationships.")
            # Optionally merge directly into the main store or return
            # self.store.graph.update(parsed_store.graph) 
            # self.store.entity_index.update(parsed_store.entity_index)
            # self.store.relationship_index.update(parsed_store.relationship_index)
            return parsed_store
        except FileNotFoundError:
            logger.error(f"Error parsing PDF: File not found at {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error parsing PDF '{file_path}': {e}")
            return None

    def explain_query_result(self, query_result: QueryResult) -> Dict[str, Any]:
        """Generates explanations for a given query result using the GraphExplainer.
        
        Args:
            query_result: The QueryResult object to explain.
            
        Returns:
            A dictionary containing various explanation components (saliency, etc.).
        """
        return self.explainer.explain_query_result(query_result)
