"""PDF processing agent implementation.

This module provides functionality for processing PDF documents and extracting their content
into the knowledge graph. The PDFProcessingAgent handles:
- PDF text extraction
- Document entity creation
- Knowledge store updates
- Unique document ID generation
- Error handling and logging

Dependencies:
    - pypdf: For PDF parsing and text extraction
    - hashlib: For generating unique document IDs
    - logging: For operation logging
"""
import logging
from typing import Dict, Any, List
from cognisgraph.agents.base_agent import BaseAgent
from cognisgraph.core.knowledge_store import KnowledgeStore
from cognisgraph.nlp.pdf_parser import PDFParser
from cognisgraph.core.entity import Entity
from cognisgraph.core.relationship import Relationship
import hashlib
from pathlib import Path
import pypdf

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> List[str]:
    """Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of strings, one per page
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        ValueError: If the file is not a valid PDF
    """
    try:
        # Validate file exists
        if not Path(pdf_path).is_file():
            raise FileNotFoundError("File not found")
            
        # Open and validate PDF
        with open(pdf_path, 'rb') as file:
            if file.read(4) != b'%PDF':
                raise ValueError("Invalid PDF")
            file.seek(0)
            
            # Extract text from each page
            reader = pypdf.PdfReader(file)
            if len(reader.pages) == 0:
                raise ValueError("Invalid PDF")
                
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    pages.append(text)
                    
            return pages
            
    except (pypdf.errors.PdfReadError, ValueError) as e:
        logger.error(f"Invalid PDF: {str(e)}")
        raise ValueError("Invalid PDF")
    except FileNotFoundError:
        logger.error(f"File not found: {pdf_path}")
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise

class PDFProcessingAgent(BaseAgent):
    """Agent responsible for processing PDF documents and storing their content in the knowledge graph.
    
    This agent extracts text from PDF documents, creates document entities for each page,
    and stores them in the knowledge graph. It handles:
    - PDF validation and text extraction
    - Unique document ID generation
    - Entity creation and storage
    - Duplicate detection and handling
    - Error handling and logging
    
    Attributes:
        knowledge_store (KnowledgeStore): The shared knowledge store instance for storing entities
        context (dict): Agent's context for maintaining state during processing
    """
    
    def __init__(self, knowledge_store: KnowledgeStore, llm: Any = None):
        """Initialize the PDF processing agent.
        
        Args:
            knowledge_store: Shared knowledge store instance for storing extracted entities
            llm: Optional language model for entity extraction. If None, uses spaCy.
        """
        super().__init__(knowledge_store)
        self.pdf_parser = PDFParser(llm)
        logger.info("PDFProcessingAgent initialized")
    
    def _generate_doc_id(self, pdf_path: str, page_num: int, content: str) -> str:
        """Generate a unique document ID for a PDF page.
        
        Creates a deterministic but unique ID for each page of a PDF document
        by combining the file path, page number, and content into a hash.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number in the PDF
            content: Text content of the page
            
        Returns:
            A unique document ID in the format "doc_<page_num>_<hash>"
        """
        # Create a unique string combining file path, page number and content
        unique_str = f"{pdf_path}_{page_num}_{content}"
        # Generate SHA-256 hash and take first 16 chars
        hash_obj = hashlib.sha256(unique_str.encode())
        return f"doc_{page_num}_{hash_obj.hexdigest()[:16]}"
    
    async def process(self, file_path: str) -> Dict[str, Any]:
        """Process a PDF file and extract entities and relationships.

        Args:
            file_path: Path to the PDF file

        Returns:
            A dictionary containing:
                - status: "success" or "error"
                - message: Error message if status is "error"
                - data: Dictionary with entities, relationships, and text
        """
        try:
            # Parse the PDF
            result = await self.pdf_parser.parse_pdf(file_path)
            
            # Extract entities and relationships from the result
            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            text = result.get("text", "")
            
            if not entities:
                return {
                    "status": "error",
                    "message": "No entities found in PDF",
                    "data": {
                        "entities": [],
                        "relationships": [],
                        "text": text,
                        "pdf_path": file_path
                    }
                }

            # Add entities and relationships to knowledge store
            for entity_dict in entities:
                entity = Entity(
                    id=entity_dict["id"],
                    type=entity_dict["type"],
                    properties=entity_dict["properties"]
                )
                self.knowledge_store.add_entity(entity)
            
            for rel_dict in relationships:
                relationship = Relationship(
                    source=rel_dict["source"],
                    target=rel_dict["target"],
                    type=rel_dict["type"],
                    properties=rel_dict.get("properties", {})
                )
                self.knowledge_store.add_relationship(relationship)

            return {
                "status": "success",
                "data": {
                    "text": text,
                    "entities": entities,
                    "relationships": relationships,
                    "pdf_path": file_path
                }
            }
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "data": {
                    "entities": [],
                    "relationships": [],
                    "text": "",
                    "pdf_path": file_path
                }
            }
    
    def reset(self) -> None:
        """Reset the agent's state."""
        super().reset()
        logger.info("PDFProcessingAgent reset") 