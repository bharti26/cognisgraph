"""PDF parser implementation."""
import logging
from typing import Dict, List, Optional, Any, Tuple
from langchain_core.messages import AIMessage
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity
from cognisgraph.core.relationship import Relationship
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pathlib import Path
import pypdf
from cognisgraph.nlp.entity_extractor import EntityExtractor
from cognisgraph.nlp.spacy_entity_extractor import SpacyEntityExtractor
import os
import uuid

logger = logging.getLogger(__name__)

class PDFParser:
    """Parser for extracting information from PDF documents."""
    
    def __init__(self, llm=None):
        """Initialize the PDF parser.
        
        Args:
            llm: Optional language model for entity extraction (ignored, we always use spaCy)
        """
        self.logger = logging.getLogger(__name__)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.entity_extractor = SpacyEntityExtractor()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If the PDF file does not exist
            ValueError: If the file is not a valid PDF or empty
        """
        try:
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)
                if len(reader.pages) == 0:
                    raise ValueError("Invalid PDF: Empty document")
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
                return text.strip()
        except Exception as e:
            error_msg = str(e)
            if "empty file" in error_msg.lower():
                raise ValueError("Invalid PDF: Empty file")
            elif "invalid pdf" in error_msg.lower():
                raise ValueError("Invalid PDF: Malformed document")
            else:
                raise ValueError(f"Invalid PDF: {error_msg}")
    
    async def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse a PDF file to extract entities and relationships.

        Args:
            file_path: Path to the PDF file

        Returns:
            A dictionary containing:
                - text: The extracted text
                - entities: List of extracted entities
                - relationships: List of extracted relationships
        """
        try:
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"text": "", "entities": [], "relationships": []}

            # Clean the text
            text = " ".join(text.split())

            # Extract entities and relationships using spaCy
            try:
                # Note: extract() is now synchronous, no need to await
                entities, relationships = self.entity_extractor.extract(text)
                
                # Always add a document entity
                if not any(e["type"] == "Document" for e in entities):
                    entities.append({
                        "id": "doc1",
                        "type": "Document",
                        "properties": {
                            "title": "Document",
                            "content": text[:1000] + "..." if len(text) > 1000 else text
                        }
                    })
                
            except Exception as e:
                logger.warning(f"Error extracting entities: {str(e)}, returning empty lists")
                entities, relationships = [], []

            return {
                "text": text,
                "entities": entities,
                "relationships": relationships
            }
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise