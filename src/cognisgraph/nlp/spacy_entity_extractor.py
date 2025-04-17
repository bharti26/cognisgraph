"""Entity and relationship extraction using spaCy."""
import logging
from typing import Dict, List, Any, Tuple
import spacy
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship

logger = logging.getLogger(__name__)

class SpacyEntityExtractor:
    """Entity extractor using spaCy for NLP processing."""
    
    def __init__(self):
        """Initialize the spaCy entity extractor."""
        self.logger = logging.getLogger(__name__)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("Downloading spaCy model 'en_core_web_sm'...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
    def extract(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract entities and relationships from text using spaCy.
        
        Args:
            text: Input text to process
            
        Returns:
            Tuple of (entities, relationships) where:
            - entities: List of entity dictionaries
            - relationships: List of relationship dictionaries
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Always add a document entity first
            entities = [{
                "id": "doc1",
                "type": "Document",
                "properties": {
                    "name": "Document",
                    "text": text[:100] + "..." if len(text) > 100 else text
                }
            }]
            
            # Extract other entities
            for ent in doc.ents:
                entities.append({
                    "id": f"ent_{len(entities)}",
                    "type": self._map_entity_type(ent.label_),
                    "properties": {
                        "name": ent.text,
                        "start": ent.start_char,
                        "end": ent.end_char
                    }
                })
            
            # Extract relationships (simple co-occurrence based)
            relationships = []
            for i, ent1 in enumerate(doc.ents):
                for j, ent2 in enumerate(doc.ents[i+1:], i+1):
                    # Check if entities are in the same sentence
                    if ent1.sent == ent2.sent:
                        relationships.append({
                            "source": f"ent_{i+1}",  # +1 because of doc entity
                            "target": f"ent_{j+1}",  # +1 because of doc entity
                            "type": "RELATED_TO",
                            "properties": {
                                "sentence": ent1.sent.text
                            }
                        })
            
            # Add relationships between document and other entities
            for i, ent in enumerate(doc.ents):
                relationships.append({
                    "source": "doc1",
                    "target": f"ent_{i+1}",  # +1 because of doc entity
                    "type": "CONTAINS",
                    "properties": {
                        "sentence": ent.sent.text
                    }
                })
            
            return entities, relationships
            
        except Exception as e:
            self.logger.error(f"Error in spaCy extraction: {str(e)}")
            # Return at least a document entity even in case of error
            return [{
                "id": "doc1",
                "type": "Document",
                "properties": {
                    "name": "Document",
                    "text": text[:100] + "..." if len(text) > 100 else text
                }
            }], []
    
    def _map_entity_type(self, spacy_type: str) -> str:
        """Map spaCy entity types to our entity types."""
        mapping = {
            "PERSON": "Person",
            "ORG": "Organization",
            "GPE": "Location",
            "LOC": "Location",
            "DATE": "Date",
            "TIME": "Time",
            "MONEY": "Money",
            "PERCENT": "Percentage",
            "QUANTITY": "Quantity",
            "CARDINAL": "Number",
            "ORDINAL": "Number",
            "NORP": "Group",
            "FAC": "Facility",
            "PRODUCT": "Product",
            "EVENT": "Event",
            "WORK_OF_ART": "Artifact",
            "LAW": "Law",
            "LANGUAGE": "Language",
            "MISC": "Miscellaneous"
        }
        return mapping.get(spacy_type, "Miscellaneous")
    
    def _map_relationship_type(self, dep_type: str) -> str:
        """Map dependency types to relationship types."""
        type_map = {
            "nsubj": "subject_of",
            "dobj": "object_of",
            "pobj": "object_of"
        }
        return type_map.get(dep_type, "related_to") 