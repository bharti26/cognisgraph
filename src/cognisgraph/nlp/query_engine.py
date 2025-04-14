import logging
from typing import Dict, List, Any, Optional
from cognisgraph.core.knowledge_store import KnowledgeStore
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from functools import lru_cache
import concurrent.futures
import time
import networkx as nx

logger = logging.getLogger(__name__)

class QueryEngine:
    """Engine for processing natural language queries against the knowledge graph."""
    
    def __init__(self, knowledge_store: Optional[KnowledgeStore] = None, max_chunk_size: int = 1000):
        """Initialize the query engine."""
        self.logger = logger
        self.knowledge_store = knowledge_store
        self.max_chunk_size = max_chunk_size
        
        # Initialize LLM with proper async support
        self.llm = OllamaLLM(
            model="llama2",
            temperature=0.1,
            top_p=0.9,
            repeat_penalty=1.1,
            streaming=False  # Disable streaming for better async support
        )
        
        # Cache for formatted graph data and prompts
        self._cached_graph_data = None
        self._cached_entities = None
        self._cached_relationships = None
        self._cached_prompts = {}
        
        # Timing metrics
        self._last_query_time = 0
        self._last_llm_time = 0
        self._last_format_time = 0
        
        # Define the prompt template with more concise format
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Answer questions using only the knowledge graph data below. Be clear and concise.
            
            Knowledge Graph:
            {graph_data}
            
            Guidelines:
            - Use only provided information
            - State "insufficient information" if needed
            - Include entity relationships when relevant"""),
            ("human", "{query}")
        ])
    
    @lru_cache(maxsize=100)
    def _format_graph_data(self, entities: tuple, relationships: tuple) -> str:
        """Format graph data for the prompt with caching."""
        if (entities, relationships) == (self._cached_entities, self._cached_relationships):
            return self._cached_graph_data
            
        start_time = time.time()
        entity_str = "\n".join([
            f"- Entity: {entity.id}\n  Type: {entity.type}\n  Properties: {entity.properties}"
            for entity in entities
        ])
        relationship_str = "\n".join([
            f"- {rel.source} -> {rel.target}\n  Type: {rel.type}\n  Properties: {rel.properties}"
            for rel in relationships
        ])
        self._last_format_time = time.time() - start_time
        return f"Entities:\n{entity_str}\n\nRelationships:\n{relationship_str}"
    
    def _chunk_graph_data(self, graph_data: str) -> List[str]:
        """Split graph data into manageable chunks."""
        chunks = []
        lines = graph_data.split("\n")
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > self.max_chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(line)
            current_size += line_size
            
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
    
    @lru_cache(maxsize=50)
    def _get_cached_prompt(self, query: str, graph_data_hash: str) -> List[Dict]:
        """Get cached prompt if available."""
        return self._cached_prompts.get((query, graph_data_hash))
    
    def _get_relationships_parallel(self, entity_ids: List[str], batch_size: int = 10) -> List[Any]:
        """Get relationships for multiple entities in parallel with batching."""
        start_time = time.time()
        relationships = []
        
        # Process entities in batches
        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i:i + batch_size]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.knowledge_store.get_relationships, entity_id) 
                          for entity_id in batch]
                for future in concurrent.futures.as_completed(futures):
                    relationships.extend(future.result())
        
        self._last_query_time = time.time() - start_time
        return relationships
    
    def _validate_response(self, response: str) -> str:
        """Validate and clean the LLM response."""
        # Remove any markdown formatting
        response = response.replace("```", "")
        
        # Ensure response is not empty
        if not response.strip():
            return "I don't have enough information to answer that question."
            
        return response.strip()
    
    async def execute_query(
        self,
        query: str,
        store: Optional[KnowledgeStore] = None
    ) -> Dict[str, Any]:
        """Execute a query against the knowledge graph."""
        start_time = time.time()
        
        try:
            # Validate input
            if not query or not query.strip():
                return {
                    "status": "error",
                    "error": "Query cannot be empty"
                }
            
            # Use provided store or default
            knowledge_store = store or self.knowledge_store
            
            # Check if knowledge store has data
            if not knowledge_store or not knowledge_store.get_entities():
                return {
                    "status": "error",
                    "error": "No knowledge available. Please upload some documents first."
                }
            
            # Process query
            result = await self.process_query(query, knowledge_store)
            
            # If process_query returned an error, return it directly
            if result["status"] == "error":
                return result
            
            # Calculate confidence
            confidence = min(0.9, 0.7 + (0.1 * len(knowledge_store.get_entities()) / 100))
            
            # Calculate centrality scores
            graph = knowledge_store.get_graph()
            centrality_scores = {}
            for node in graph.nodes():
                centrality_scores[node] = {
                    "degree_centrality": nx.degree_centrality(graph).get(node, 0.0),
                    "betweenness_centrality": nx.betweenness_centrality(graph).get(node, 0.0),
                    "closeness_centrality": nx.closeness_centrality(graph).get(node, 0.0)
                }
                # Try eigenvector centrality with fallback
                try:
                    centrality_scores[node]["eigenvector_centrality"] = nx.eigenvector_centrality(graph).get(node, 0.0)
                except nx.PowerIterationFailedConvergence:
                    centrality_scores[node]["eigenvector_centrality"] = 0.0
                    logger.warning(f"Eigenvector centrality failed to converge for node {node}, using fallback value")
            
            # Format response
            return {
                "status": "success",
                "answer": result["answer"],
                "confidence": confidence,
                "explanation": result["explanation"],
                "entities": result["entities"],
                "relationships": result["relationships"],
                "saliency": {
                    "centrality_scores": centrality_scores
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing query: {str(e)}",
                "data": {
                    "entities": [],
                    "relationships": []
                }
            }
    
    async def process_query(self, query: str, knowledge_store: Optional[KnowledgeStore] = None) -> Dict[str, Any]:
        """Process a query using the knowledge graph."""
        try:
            # Use provided store or default
            knowledge_store = knowledge_store or self.knowledge_store
            
            # Get entities and relationships
            entities = knowledge_store.get_entities()
            relationships = knowledge_store.get_relationships()
            
            # Format graph data
            graph_data = self._format_graph_data(tuple(entities), tuple(relationships))
            
            # Create prompt
            prompt = self.prompt_template.format_messages(
                graph_data=graph_data,
                query=query
            )
            
            # Process with LLM
            start_time = time.time()
            response = await self.llm.ainvoke(prompt)
            self._last_llm_time = time.time() - start_time
            
            # Handle response content
            if isinstance(response, AIMessage):
                content = response.content
            else:
                content = str(response)
            
            # Validate and process response
            content = self._validate_response(content)
            
            return {
                "status": "success",
                "answer": content,
                "explanation": "Generated from knowledge graph data",
                "entities": [{"id": e.id, "type": e.type} for e in entities],
                "relationships": [{"source": r.source, "target": r.target, "type": r.type} for r in relationships]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_metrics(self) -> Dict[str, float]:
        """Get timing metrics for the last query."""
        return {
            "llm_time": self._last_llm_time,
            "format_time": self._last_format_time,
            "total_time": self._last_llm_time + self._last_format_time
        } 