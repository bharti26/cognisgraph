"""Entity and relationship extraction from text."""
import logging
import json
from typing import Dict, List, Any, Tuple
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
import re

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Extracts entities and relationships from text using LLM."""
    
    def __init__(self, llm: BaseLanguageModel):
        """Initialize the entity extractor.
        
        Args:
            llm: Language model for entity extraction
        """
        self.llm = llm
        self.entity_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting entities and relationships from text.
            Extract all important entities and their relationships from the given text.
            For each entity, identify its type and properties.
            For each relationship, identify the source, target, type and properties.
            
            Format your response as a JSON object with two keys:
            - "entities": List of entities, each with id, type, and properties
            - "relationships": List of relationships, each with source, target, type, and properties
            
            Properties should be a dictionary of key-value pairs, not a list.
            Use consistent IDs for entities that appear multiple times.
            
            IMPORTANT: 
            1. Your response must be valid JSON with NO whitespace or newlines before or after the JSON object.
            2. Do not include any text, comments, or explanations - only the JSON object.
            3. The JSON should be on a single line with no extra spaces or newlines.
            4. ALWAYS include at least one entity of type "document" with properties like title, content, etc.
            5. If no other entities are found, still return the document entity.
            6. Never return just a key like "entities" or "relationships" - always return a complete JSON object.
            
            Example response (all on one line):
            {"entities":[{"id":"doc1","type":"document","properties":{"title":"Sample Document","content":"..."}},{"id":"entity1","type":"person","properties":{"name":"John","age":30}}],"relationships":[{"source":"entity1","target":"doc1","type":"authored","properties":{"date":"2020"}}]}
            
            Example minimal response (all on one line):
            {"entities":[{"id":"doc1","type":"document","properties":{"title":"Untitled Document","content":"..."}}],"relationships":[]}
            """),
            ("human", "{text}")
        ])
        
    def _clean_json_str(self, json_str: str) -> str:
        """Clean and validate JSON string before parsing.
        
        Args:
            json_str: Raw JSON string from LLM
            
        Returns:
            Cleaned JSON string that can be parsed
            
        Raises:
            ValueError: If JSON is invalid or missing required keys
        """
        if not json_str:
            logger.warning("Empty JSON string, returning default empty response")
            return '{"entities":[],"relationships":[]}'
            
        # First strip all whitespace including newlines
        cleaned = json_str.strip()
        
        # Special case: if response is just "entities" or "relationships" or similar
        if cleaned.lower() in ['"entities"', '"relationships"', 'entities', 'relationships']:
            logger.warning(f"Received minimal response '{cleaned}', returning default empty response")
            return '{"entities":[],"relationships":[]}'
        
        # If the string starts with a newline followed by a quote, remove the newline
        if cleaned.startswith('\n"'):
            cleaned = cleaned[1:]
        
        try:
            # Try to parse as is first
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            try:
                # Find first { and last }
                start_idx = cleaned.find('{')
                end_idx = cleaned.rfind('}')
                
                if start_idx == -1 or end_idx == -1:
                    # No braces found - check if it's a raw key-value format
                    if cleaned.startswith('"entities"') or cleaned.startswith('"relationships"'):
                        logger.warning("Found raw key-value format, attempting to fix")
                        # Return default empty response
                        return '{"entities":[],"relationships":[]}'
                    else:
                        logger.error(f"Invalid JSON format: {cleaned}")
                        return '{"entities":[],"relationships":[]}'
                else:
                    # Extract content between braces
                    cleaned = cleaned[start_idx:end_idx + 1]
                
                # Clean trailing commas
                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                
                # Final strip of extra whitespace
                cleaned = cleaned.strip()
                
                # Validate the cleaned JSON
                try:
                    parsed = json.loads(cleaned)
                    # Ensure both entities and relationships keys exist
                    if "entities" not in parsed:
                        parsed["entities"] = []
                    if "relationships" not in parsed:
                        parsed["relationships"] = []
                    return json.dumps(parsed)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse cleaned JSON: {cleaned}")
                    return '{"entities":[],"relationships":[]}'
                
            except Exception as e:
                logger.error(f"Error cleaning JSON string: {str(e)}")
                logger.debug(f"Original JSON string: {json_str}")
                return '{"entities":[],"relationships":[]}'
        
    async def extract(self, input_or_response) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract entities and relationships from text or LLM response.

        Args:
            input_or_response: Can be one of:
                - Raw text to extract entities from
                - A string containing JSON from LLM
                - A dictionary with "entities" and "relationships" keys
                - An object with a content attribute containing any of the above

        Returns:
            A tuple of (entities, relationships) lists
        """
        try:
            # If input is raw text, call LLM to extract entities
            if isinstance(input_or_response, str):
                # First try to parse as JSON
                try:
                    json.loads(input_or_response)
                    # If it's valid JSON, treat it as a response
                    response = input_or_response
                except json.JSONDecodeError:
                    # If not JSON, treat it as raw text
                    logger.info(f"Processing raw text input: {input_or_response[:100]}...")
                    messages = self.entity_prompt.format_messages(text=input_or_response)
                    response = await self.llm.invoke(messages)
                    # Get content from AIMessage
                    if hasattr(response, 'content'):
                        response = response.content
                    else:
                        logger.error("LLM response has no content attribute")
                        # Return default document entity
                        return [{
                            "id": "doc1",
                            "type": "document",
                            "properties": {
                                "title": "Untitled Document",
                                "content": input_or_response
                            }
                        }], []

            # If response has content attribute, use that
            if hasattr(response, 'content'):
                response = response.content

            # Handle dictionary response
            if isinstance(response, dict):
                entities = response.get("entities", [])
                relationships = response.get("relationships", [])
                if not entities:
                    # Create a default document entity
                    entities = [{
                        "id": "doc1",
                        "type": "document",
                        "properties": {
                            "title": "Untitled Document",
                            "content": str(input_or_response)
                        }
                    }]
                    logger.warning("No entities found in response dictionary, created default document entity")
                return entities, relationships

            # If response is a string, try to parse it as JSON
            if isinstance(response, str):
                # Clean the response string first
                response = response.strip()
                
                # Special case: if response is just "entities" or similar
                if response.lower() in ['"entities"', '"relationships"', 'entities', 'relationships']:
                    logger.warning(f"Received minimal response: {response}, creating default document entity")
                    return [{
                        "id": "doc1",
                        "type": "document",
                        "properties": {
                            "title": "Untitled Document",
                            "content": str(input_or_response)
                        }
                    }], []

                # Clean and validate the JSON string
                cleaned_response = self._clean_json_str(response)
                try:
                    parsed = json.loads(cleaned_response)
                    entities = parsed.get("entities", [])
                    relationships = parsed.get("relationships", [])
                    
                    # Ensure we have at least one document entity
                    if not entities:
                        entities = [{
                            "id": "doc1",
                            "type": "document",
                            "properties": {
                                "title": "Untitled Document",
                                "content": str(input_or_response)
                            }
                        }]
                        logger.warning("No entities found in parsed JSON, created default document entity")
                    
                    return entities, relationships
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    logger.debug(f"Response was: {response}")
                    # Return default document entity
                    return [{
                        "id": "doc1",
                        "type": "document",
                        "properties": {
                            "title": "Untitled Document",
                            "content": str(input_or_response)
                        }
                    }], []

            # If we get here, something unexpected happened
            logger.error(f"Unexpected response type: {type(response)}")
            # Return default document entity
            return [{
                "id": "doc1",
                "type": "document",
                "properties": {
                    "title": "Untitled Document",
                    "content": str(input_or_response)
                }
            }], []

        except Exception as e:
            logger.error(f"Error in extract method: {str(e)}")
            # Return default document entity
            return [{
                "id": "doc1",
                "type": "document",
                "properties": {
                    "title": "Untitled Document",
                    "content": str(input_or_response)
                }
            }], []