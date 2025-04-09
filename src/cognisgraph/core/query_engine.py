from typing import Dict, Any, List, Optional
import torch
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import numpy as np
import logging # Import logging
from .knowledge_store import KnowledgeStore # Assuming relative import works
import threading # Import threading for thread-safe initialization

logger = logging.getLogger(__name__) # Initialize logger

# Module-level singleton for the encoder
_encoder = None
_encoder_lock = threading.Lock() # Lock for thread-safe initialization

def get_encoder():
    """Gets the singleton SentenceTransformer instance, initializing it thread-safely."""
    global _encoder
    if _encoder is None:
        with _encoder_lock:
            if _encoder is None: # Double-check locking
                try:
                    # Determine device dynamically
                    device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
                    logger.info(f"Initializing SentenceTransformer on device: {device}")
                    _encoder = SentenceTransformer('all-MiniLM-L6-v2', device=device)
                except Exception as e:
                    logger.error(f"Failed to initialize SentenceTransformer: {e}", exc_info=True)
                    raise # Re-raise after logging
    return _encoder

class QueryResult(BaseModel):
    """Represents the structured result of a query processed by the QueryEngine.
    
    Attributes:
        query: The original query string.
        answer: The generated natural language answer.
        confidence: A numerical score indicating the confidence in the answer (0.0 to 1.0).
        evidence: A list of dictionaries, each representing an entity or relationship
                  that supports the answer, including relevance scores.
        explanation: An optional dictionary containing explainable AI (XAI) insights.
    """
    query: str
    answer: str
    confidence: float
    evidence: List[Dict[str, Any]]
    explanation: Optional[Dict[str, Any]]

class QueryEngine:
    """Processes natural language queries against a KnowledgeStore.
    
    Uses sentence embeddings to find relevant entities and relationships,
    generates answers, gathers evidence, and provides explanations.
    """
    def __init__(self, knowledge_store: KnowledgeStore):
        """Initializes the QueryEngine.

        Args:
            knowledge_store: An instance of KnowledgeStore to query against.
        """
        if not isinstance(knowledge_store, KnowledgeStore):
            raise TypeError("knowledge_store must be an instance of KnowledgeStore")
        self.knowledge_store = knowledge_store
        self.cache: Dict[str, QueryResult] = {} # Basic query caching
        logger.debug("QueryEngine initialized.")

    def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Processes a query: finds relevant info, generates answer & explanation.

        Args:
            query: The natural language query string.
            context: Optional context dictionary (currently unused).

        Returns:
            A QueryResult object.
            
        Raises:
            ValueError: If the query is invalid.
            RuntimeError: If the sentence encoder fails.
        """
        if not query or not isinstance(query, str):
             raise ValueError("Query must be a non-empty string.")
             
        # Check cache first (simple exact match)
        if query in self.cache:
             logger.info(f"Returning cached result for query: '{query[:50]}...'")
             return self.cache[query]

        logger.info(f"Processing query: '{query[:50]}...'")
        try:
            # Encode query
            query_embedding = get_encoder().encode(query, convert_to_tensor=True)
        except Exception as e:
            logger.error(f"Failed to encode query '{query}': {e}", exc_info=True)
            raise RuntimeError("Sentence encoder failed during query processing") from e

        # Find relevant entities
        relevant_entities = self._find_relevant_entities(query_embedding)
        logger.debug(f"Found {len(relevant_entities)} relevant entities.")
        
        # Find relevant relationships
        relevant_relationships = self._find_relevant_relationships(
            relevant_entities,
            query
        )
        logger.debug(f"Found {len(relevant_relationships)} relevant relationships.")

        # Generate answer
        answer, confidence = self._generate_answer(
            query,
            relevant_entities,
            relevant_relationships,
            context # Context is passed but currently unused in _generate_answer
        )
        logger.debug(f"Generated answer with confidence {confidence:.2f}")
        
        # Gather evidence
        evidence = self._gather_evidence(relevant_entities, relevant_relationships)
        logger.debug(f"Gathered {len(evidence)} pieces of evidence.")
        
        # Generate explanation (currently placeholder)
        explanation = self._generate_explanation(
            query,
            relevant_entities,
            relevant_relationships,
            answer
        )
        logger.debug("Generated explanation structure.")

        result = QueryResult(
            query=query,
            answer=answer,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation
        )
        
        # Cache result
        self.cache[query] = result
        
        return result
    
    def _find_relevant_entities(
        self,
        query_embedding: torch.Tensor,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Finds entities most similar to the query embedding.

        Args:
            query_embedding: The embedding vector of the query.
            top_k: The maximum number of relevant entities to return.

        Returns:
            A list of dictionaries, each containing an 'entity' object and its 
            'similarity' score, sorted by similarity descending.
        """
        if self.knowledge_store.entity_index is None:
            logger.warning("Entity index is None, cannot find relevant entities.")
            return []
            
        relevant_entities = []
        num_entities = len(self.knowledge_store.entity_index)
        if num_entities == 0:
             logger.warning("Knowledge store has no entities to search.")
             return []
             
        logger.debug(f"Calculating similarity against {num_entities} entities...")
        
        all_entity_texts = []
        all_entities = []
        for entity_id, entity in self.knowledge_store.entity_index.items():
            entity_text = f"{entity.type} {entity.id} " + " ".join(
                f"{k} {v}" for k, v in entity.properties.items()
            )
            all_entity_texts.append(entity_text)
            all_entities.append(entity)

        try:
             # Encode all entity texts in batch for efficiency
             entity_embeddings = get_encoder().encode(all_entity_texts, convert_to_tensor=True)
             
             # Compute cosine similarities in batch
             similarities = torch.cosine_similarity(query_embedding.unsqueeze(0), entity_embeddings, dim=1)
             
             # Combine entities with their scores
             for entity, similarity in zip(all_entities, similarities):
                 relevant_entities.append({
                     "entity": entity,
                     "similarity": similarity.item()
                 })
                 
        except Exception as e:
            logger.error(f"Error during entity embedding or similarity calculation: {e}", exc_info=True)
            # Fallback to individual calculation if batch fails?
            return [] # Or handle error differently

        # Sort by similarity and return top_k
        relevant_entities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Format scores for logging
        scores_log = [(e['entity'].id, f"{e['similarity']:.2f}") for e in relevant_entities[:top_k]]
        logger.debug(f"Top {top_k} relevant entities found (scores): {scores_log}")
        return relevant_entities[:top_k]

    def _find_relevant_relationships(
        self,
        relevant_entities: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Finds relationships connected to relevant entities whose type matches query terms.
        
        Avoids adding duplicate relationships if found via different entities.

        Args:
            relevant_entities: A list of relevant entity data (including similarity scores).
            query: The original query string.

        Returns:
            A list of unique relationship data dictionaries, sorted by the 
            similarity score of the entity through which they were found.
        """
        relevant_relationships_data = {} # Use dict to store unique relationships by key
        added_relationship_keys = set() # Keep track of added relationship keys
        
        for entity_data in relevant_entities:
            entity = entity_data["entity"]
            try:
                relationships = self.knowledge_store.get_relationships(entity.id)
            except Exception as e:
                 logger.warning(f"Error getting relationships for entity {entity.id}: {e}")
                 continue # Skip this entity if relationships can't be retrieved
            
            for relationship in relationships:
                # Generate a unique key for the relationship (order-independent)
                # Sort source/target to handle directionality consistently for indexing
                try:
                     nodes = sorted([relationship.source, relationship.target])
                     rel_key = f"{nodes[0]}_{relationship.type}_{nodes[1]}"
                except Exception as e:
                     logger.warning(f"Could not generate key for relationship {relationship}: {e}")
                     continue # Skip if key cannot be generated
                
                # Check if this relationship (regardless of direction found) is already added
                if rel_key in added_relationship_keys:
                    continue

                # Check if relationship type is relevant to the query
                try:
                     type_matches = any(word in query.lower() for word in relationship.type.lower().split('_'))
                except AttributeError:
                     logger.warning(f"Relationship type is not a string or is missing for {rel_key}")
                     type_matches = False # Cannot match if type is invalid
                     
                if type_matches:
                    # Store relationship data using the key, potentially updating similarity if a more relevant entity found it
                    current_similarity = relevant_relationships_data.get(rel_key, {"source_similarity": 0.0})["source_similarity"]
                    # Ensure similarity is float before comparison
                    entity_similarity = float(entity_data.get("similarity", 0.0))
                    
                    if entity_similarity > current_similarity:
                         relevant_relationships_data[rel_key] = {
                             "relationship": relationship,
                             "source_similarity": entity_similarity # Use the float value
                         }
                    added_relationship_keys.add(rel_key) # Mark as added
        
        # Return the unique relationships found, sorted by relevance
        final_list = list(relevant_relationships_data.values())
        final_list.sort(key=lambda x: x["source_similarity"], reverse=True)
        return final_list

    def _generate_answer(
        self,
        query: str,
        relevant_entities: List[Dict[str, Any]],
        relevant_relationships: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, float]:
        """Generates a simple answer string based on the most relevant findings.

        Args:
            query: The original query string.
            relevant_entities: List of relevant entity data.
            relevant_relationships: List of relevant relationship data.
            context: Optional context (currently unused).

        Returns:
            A tuple containing the answer string and an average confidence score.
        """
        if not relevant_entities:
            logger.info("Cannot generate answer: No relevant entities found.")
            return "I don't have enough information to answer that question.", 0.0
        
        answer_parts = []
        confidence_scores = []
        added_info = set() # Track added info to avoid redundancy
        
        # Add information about the most relevant entities
        for entity_data in relevant_entities[:3]: # Limit to top 3 entities
            entity = entity_data["entity"]
            similarity = float(entity_data.get("similarity", 0.0))
            entity_info = f"{entity.id} ({entity.type}) properties: {entity.properties}"
            if entity_info not in added_info:
                 answer_parts.append(entity_info)
                 confidence_scores.append(similarity)
                 added_info.add(entity_info)
        
        # Add information about relationships if available
        if relevant_relationships:
            answer_parts.append("\nRelevant relationships:")
            for rel_data in relevant_relationships[:3]: # Limit to top 3 relationships
                rel = rel_data["relationship"]
                similarity = float(rel_data.get("source_similarity", 0.0))
                rel_info = f"- {rel.source} --[{rel.type}]--> {rel.target} ({rel.properties})"
                if rel_info not in added_info:
                     answer_parts.append(rel_info)
                     confidence_scores.append(similarity)
                     added_info.add(rel_info)
        
        if not answer_parts: # Handle cases where only low-similarity items were found
             logger.info("Generated answer is empty, returning default.")
             return "Based on the available information, I couldn't construct a specific answer.", 0.0
             
        answer = " ".join(answer_parts)
        confidence = float(np.mean(confidence_scores)) if confidence_scores else 0.0
        
        logger.info(f"Generated answer: '{answer[:100]}...'")
        return answer, confidence

    def _generate_explanation(
        self,
        query: str,
        relevant_entities: List[Dict[str, Any]],
        relevant_relationships: List[Dict[str, Any]],
        answer: str
    ) -> Dict[str, Any]:
        """Generates a placeholder explanation structure.

        Args:
            query: The original query string.
            relevant_entities: List of relevant entity data.
            relevant_relationships: List of relevant relationship data.
            answer: The generated answer string.

        Returns:
            A dictionary containing placeholder explanation data.
        """ 
        # TODO: Replace placeholders with actual XAI logic from explainer module
        logger.warning("Generating placeholder explanation. Integrate with GraphExplainer.")
        # Example structure, needs real data from explainer
        explanation = {
            "saliency": {
                "centrality_scores": {
                    e["entity"].id: {"placeholder_centrality": round(e["similarity"], 2)}
                    for e in relevant_entities
                },
                "path_importance": {},
                "community_role": {e["entity"].id: "unknown" for e in relevant_entities}
            },
            "feature_importance": {
                 "importance_scores": {"placeholder": 1.0},
                 "ranked_features": [("placeholder", 1.0)],
                 "confidence_scores": {"placeholder": 1.0}
            },
            "rules": ["Placeholder explanation rule."]
        }
        return explanation

    def _gather_evidence(
        self,
        relevant_entities: List[Dict[str, Any]],
        relevant_relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Formats the relevant entities and relationships into an evidence list.

        Args:
            relevant_entities: List of relevant entity data.
            relevant_relationships: List of relevant relationship data.

        Returns:
            A list of dictionaries, each representing a piece of evidence.
        """
        evidence = []
        processed_ids = set() # Avoid duplicate evidence entries

        # Add entities as evidence
        for entity_data in relevant_entities:
            entity = entity_data["entity"]
            if entity.id not in processed_ids:
                evidence.append({
                    "type": "entity",
                    "id": entity.id,
                    "entity_type": entity.type, # Add entity type for clarity
                    "relevance": float(entity_data.get("similarity", 0.0)),
                    "properties": entity.properties
                })
                processed_ids.add(entity.id)
        
        # Add relationships as evidence
        for rel_data in relevant_relationships:
            rel = rel_data["relationship"]
            # Use the same key generation as in _find_relevant_relationships
            nodes = sorted([rel.source, rel.target])
            rel_key = f"{nodes[0]}_{rel.type}_{nodes[1]}"
            
            if rel_key not in processed_ids:
                evidence.append({
                    "type": "relationship",
                    "source": rel.source,
                    "target": rel.target,
                    "relationship_type": rel.type,
                    "relevance": float(rel_data.get("source_similarity", 0.0)),
                    "properties": rel.properties
                })
                processed_ids.add(rel_key)
        
        # Sort evidence by relevance score, descending
        evidence.sort(key=lambda x: x.get("relevance", 0.0), reverse=True)
        
        return evidence
