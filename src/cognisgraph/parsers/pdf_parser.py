import pypdf
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from typing import Dict, List, Tuple
import os
import re # Import regex module
import logging # Import logging
from cognisgraph.core.knowledge_store import KnowledgeStore, Entity, Relationship

logger = logging.getLogger(__name__) # Initialize logger

# Ensure NLTK data path is recognized if using a custom one
# (conftest.py should handle downloads)

# Remove global tokenizer loading
# try:
#     # Use the standard resource path for punkt
#     punkt_tokenizer = nltk.data.load('tokenizers/punkt/PY3/english.pickle')
# except LookupError:
#     print("NLTK 'punkt' tokenizer not found. Please ensure it is downloaded.")
#     # As a fallback, try downloading again, although conftest should handle this.
#     try:
#         nltk.download('punkt', quiet=True)
#         punkt_tokenizer = nltk.data.load('tokenizers/punkt/PY3/english.pickle')
#     except Exception as e:
#         print(f"Failed to load NLTK punkt tokenizer after download attempt: {e}")
#         # If it still fails, raise an error or handle appropriately
#         # For now, we might let subsequent code fail if punkt_tokenizer is not loaded.
#         punkt_tokenizer = None

class PDFParser:
    """Parses PDF documents to extract entities and relationships using NLTK.

    Uses pypdf to extract text and NLTK for basic Named Entity Recognition (NER).
    Also includes regex-based extraction for specific date patterns.
    """
    
    def __init__(self):
        """Initializes the PDF parser and loads required NLTK data.
        
        Attempts to load NLTK resources (punkt, taggers, chunkers, corpora).
        Will trigger downloads if resources are not found.
        Raises RuntimeError if essential tokenizers cannot be loaded.
        """
        logger.info("Initializing PDFParser and NLTK resources...")
        self.punkt_tokenizer = self._load_nltk_tokenizer()
        # Load other required NLTK data if not already present
        self._ensure_nltk_data([
            'averaged_perceptron_tagger', 
            'maxent_ne_chunker', 
            'words',
            'punkt_tab', # Dependency for punkt
            'averaged_perceptron_tagger_eng', # Dependency for perceptron tagger
            'maxent_ne_chunker_tab' # Dependency for maxent chunker
            ])
        logger.info("PDFParser initialized successfully.")
    
    def _load_nltk_tokenizer(self):
        """Loads the NLTK Punkt tokenizer, downloading if necessary.
        
        Returns:
            The loaded Punkt tokenizer object.
            
        Raises:
            RuntimeError: If the tokenizer cannot be loaded even after download attempt.
        """
        resource_path = 'tokenizers/punkt/PY3/english.pickle'
        try:
            logger.debug(f"Attempting to load NLTK resource: {resource_path}")
            return nltk.data.load(resource_path)
        except LookupError:
            logger.warning(f"NLTK resource '{resource_path}' not found. Attempting download of 'punkt'...")
            try:
                nltk.download('punkt', quiet=False) # Download explicitly
                # Try loading dependent resources needed by Punkt
                try:
                    nltk.data.find('tokenizers/punkt_tab/english/')
                except LookupError:
                     logger.warning("'punkt_tab' not found, attempting download...")
                     nltk.download('punkt_tab', quiet=False)
                     
                logger.info("Download complete. Reloading tokenizer...")
                return nltk.data.load(resource_path)
            except Exception as e:
                logger.error(f"FATAL: Failed to load NLTK punkt tokenizer after download: {e}", exc_info=True)
                # Raise an error or handle appropriately if critical
                raise RuntimeError("Could not initialize NLTK Punkt tokenizer") from e

    def _ensure_nltk_data(self, resources: List[str]):
        """Ensures required NLTK resources are downloaded.
        
        Checks for taggers, chunkers, and corpora.
        
        Args:
            resources: A list of NLTK resource names (e.g., 'averaged_perceptron_tagger').
        """
        for resource in resources:
            try:
                # Construct likely path based on resource type heuristic
                if 'tagger' in resource:
                    path_fragment = f'taggers/{resource}'
                elif 'chunker' in resource:
                     path_fragment = f'chunkers/{resource}'
                elif 'punkt' in resource:
                     path_fragment = f'tokenizers/{resource}'
                else:
                     path_fragment = f'corpora/{resource}'
                
                logger.debug(f"Checking for NLTK resource: {path_fragment}")
                # Use find which checks multiple locations and formats
                nltk.data.find(path_fragment)
                logger.debug(f"Resource '{resource}' found.")
            except LookupError:
                logger.warning(f"NLTK resource '{resource}' (path: {path_fragment}) not found. Attempting download...")
                try:
                    nltk.download(resource, quiet=False)
                    logger.info(f"Resource '{resource}' downloaded.")
                except Exception as e:
                    logger.error(f"Failed to download NLTK resource '{resource}': {e}", exc_info=True)
                    # Depending on the resource, you might want to raise an error

    def parse(self, file_path: str) -> Tuple[List[Dict], List[Dict]]:
        """Parse a PDF file and extract entities and relationships."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Extract text from PDF
        text = self._extract_text(file_path)
        
        # Extract entities and relationships
        if self.punkt_tokenizer is None:
             raise RuntimeError("NLTK Punkt tokenizer failed to load.")
        entities = self._extract_entities(text)
        relationships = self._extract_relationships(text, entities)
        
        return entities, relationships
    
    def _extract_text(self, file_path: str) -> str:
        """Extracts text content from a PDF file using pypdf.
        
        Args:
            file_path: The path to the PDF file.

        Returns:
            The extracted text as a single string, or an empty string if extraction fails.
        """
        text = ""
        # print(f"[DEBUG] Attempting to extract text from: {file_path}") # REMOVE DEBUG
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                # print(f"[DEBUG] PDF has {len(pdf_reader.pages)} pages.") # REMOVE DEBUG
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        # print(f"[DEBUG] Page {i+1} extracted text (first 100 chars): {page_text[:100] if page_text else 'None'}") # REMOVE DEBUG
                        if page_text:
                            text += page_text + "\n"
                    except Exception as page_e:
                        logger.warning(f"Could not extract text from page {i+1} of {file_path}: {page_e}")
        except pypdf.errors.PdfReadError as e:
             logger.error(f"Error reading PDF {file_path}: {e}", exc_info=True)
             return "" # Return empty text on error
        except FileNotFoundError:
             logger.error(f"PDF file not found during text extraction: {file_path}")
             raise # Re-raise FileNotFoundError
        except Exception as e:
             logger.error(f"An unexpected error occurred extracting text from {file_path}: {e}", exc_info=True)
             return "" # Return empty text on unexpected error
        # print(f"[DEBUG] Total extracted text (first 200 chars): {text[:200]}") # REMOVE DEBUG
        return text
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """Extracts entities from text using NLTK NER and supplements with regex for dates.

        Args:
            text: The text content to extract entities from.

        Returns:
            A list of dictionaries, where each dictionary represents an extracted entity
            with keys 'text', 'type', and 'context'.
        """
        entities = []
        if not text:
             logger.warning("Text input to _extract_entities is empty.")
             return entities
        if not self.punkt_tokenizer:
             logger.error("Punkt tokenizer not loaded on instance.")
             raise RuntimeError("PDFParser not properly initialized: Punkt tokenizer missing.")
             
        try:
             sentences = self.punkt_tokenizer.tokenize(text)
        except Exception as e:
             logger.error(f"NLTK sentence tokenization failed: {e}", exc_info=True)
             return [] # Cannot proceed without sentences
             
        logger.debug(f"Tokenized text into {len(sentences)} sentences.")

        # --- NLTK based extraction --- 
        logger.debug("Performing NLTK NER...")
        nltk_entity_count = 0
        for i, sentence in enumerate(sentences):
            try:
                tokens = word_tokenize(sentence)
                tagged = pos_tag(tokens)
                tree = ne_chunk(tagged)
            except Exception as e:
                logger.warning(f"NLTK tagging/chunking failed for sentence {i+1}: {e}. Skipping sentence NER.")
                continue # Skip sentence if NLTK processing fails
                
            # Extract named entities from the tree
            for chunk in tree:
                if hasattr(chunk, 'label'):
                    entity_type = chunk.label()
                    entity_text = ' '.join(c[0] for c in chunk)

                    # Strip trailing punctuation (e.g., period) for better matching
                    entity_text_cleaned = entity_text.rstrip('.,;:!?')

                    # Map NLTK entity types to our schema
                    mapped_type = self._map_entity_type(entity_type)
                    if mapped_type:
                        nltk_entity_count += 1
                        entities.append({
                            'text': entity_text_cleaned, # Use cleaned text
                            'type': mapped_type,
                            'context': sentence
                        })
                        
        logger.debug(f"Found {nltk_entity_count} entities using NLTK NER.")

        # --- Regex based date extraction (supplementary) --- 
        logger.debug("Performing supplementary regex date extraction...")
        date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{4})\b")
        existing_entity_texts = {e['text'] for e in entities} # Avoid adding duplicates
        regex_date_count = 0
        
        for i, sentence in enumerate(sentences):
             try:
                 matches = date_pattern.finditer(sentence)
                 for match in matches:
                     date_text = match.group(0)
                     # Check if this date text is already part of a larger extracted entity
                     # or if it's already been added as a date
                     is_substring = any(date_text in entity['text'] for entity in entities if len(entity['text']) > len(date_text))
                     if date_text not in existing_entity_texts and not is_substring:
                         regex_date_count += 1
                         entities.append({
                             'text': date_text, # Already cleaned by regex word boundary
                             'type': 'DATE',
                             'context': sentence
                         })
                         existing_entity_texts.add(date_text) # Track added dates
                         # print(f"[DEBUG] Added DATE entity via regex: {date_text}") # Optional debug
             except Exception as e:
                 logger.warning(f"Regex date matching failed for sentence {i+1}: {e}")
                 
        logger.debug(f"Found {regex_date_count} additional DATE entities using regex.")

        logger.info(f"Total entities extracted: {len(entities)}")
        return entities
    
    def _extract_relationships(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Extracts simple co-occurrence relationships between entities found in the same sentence.

        Args:
            text: The original text (unused, context is taken from entities).
            entities: A list of extracted entity dictionaries (must include 'text' and 'context').

        Returns:
            A list of dictionaries, each representing a 'related' relationship
            with keys 'source', 'target', 'type', and 'context'.
        """
        relationships = []
        if not self.punkt_tokenizer:
             logger.error("Punkt tokenizer not loaded for relationship extraction.")
             raise RuntimeError("PDFParser not properly initialized: Punkt tokenizer missing.")
             
        if not entities:
             logger.debug("No entities provided, cannot extract relationships.")
             return []

        # Group entities by their context sentence
        entities_by_sentence: Dict[str, List[Dict]] = {}
        for entity in entities:
            context = entity.get('context')
            if not context: # Skip entities without context
                 logger.warning(f"Skipping entity for relationship extraction due to missing context: {entity.get('text')}")
                 continue 
            if context not in entities_by_sentence:
                entities_by_sentence[context] = []
            entities_by_sentence[context].append(entity)
            
        logger.debug(f"Grouped entities into {len(entities_by_sentence)} sentences for relationship extraction.")

        # Iterate through sentences that have multiple entities
        rel_count = 0
        for sentence, sentence_entities in entities_by_sentence.items():
            if len(sentence_entities) >= 2:
                # Create relationships between distinct entities in the same sentence
                for i in range(len(sentence_entities)):
                    for j in range(i + 1, len(sentence_entities)):
                        ent_i = sentence_entities[i]
                        ent_j = sentence_entities[j]
                        # # print(f"[DEBUG] Comparing entities in sentence '{sentence[:30]}...': \n  i: {ent_i}\n  j: {ent_j}") # REMOVE DEBUG
                        
                        # Ensure text field exists
                        text_i = ent_i.get('text')
                        text_j = ent_j.get('text')
                        if not text_i or not text_j:
                             continue # Skip if text is missing
                             
                        # Basic check to avoid relating sub-parts of the same potential entity
                        if text_i in text_j or text_j in text_i:
                           # # print(f"[DEBUG] Skipping relationship: one text is substring of other.") # REMOVE DEBUG
                           continue

                        # # print(f"[DEBUG] Adding relationship: source='{ent_i['text']}', target='{ent_j['text']}'") # REMOVE DEBUG
                        rel_count += 1
                        relationships.append({
                            'source': text_i,
                            'target': text_j,
                            'type': 'related',  # Default relationship type
                            'context': sentence
                        })
        
        logger.info(f"Generated {rel_count} co-occurrence relationships.")
        # # print(f"[DEBUG] Final list of relationships generated by _extract_relationships: {relationships}") # REMOVE DEBUG
        return relationships
    
    def _map_entity_type(self, nltk_type: str) -> str:
        """Maps NLTK standard entity types to a custom schema.

        Args:
            nltk_type: The entity type string returned by NLTK (e.g., 'PERSON', 'GPE').

        Returns:
            The corresponding custom entity type string (e.g., 'PERSON', 'LOC') 
            or None if the type is not mapped.
        """
        type_mapping = {
            'PERSON': 'PERSON',
            'ORGANIZATION': 'ORG',
            'GPE': 'LOC',       # Geo-Political Entity
            'DATE': 'DATE',
            'MONEY': 'NUM',
            'PERCENT': 'NUM',
            'FACILITY': 'LOC',
            'LOCATION': 'LOC'
        }
        mapped = type_mapping.get(nltk_type)
        if not mapped:
            logger.debug(f"NLTK entity type '{nltk_type}' not mapped to custom schema.")
        return mapped

    def parse_pdf(self, file_path: str) -> KnowledgeStore:
        """Parses a PDF file, extracts text, entities, and relationships.

        Args:
            file_path: The full path to the PDF file.

        Returns:
            A KnowledgeStore instance populated with entities and relationships
            extracted from the PDF.
            
        Raises:
            FileNotFoundError: If the file_path does not exist.
            RuntimeError: If essential NLTK components are missing/failed to load.
            Other exceptions from pypdf or NLTK during processing.
        """
        logger.info(f"Starting to parse PDF: {file_path}")
        if not os.path.exists(file_path):
             logger.error(f"PDF file not found at path: {file_path}")
             raise FileNotFoundError(f"PDF file not found: {file_path}")
             
        # Extract text from PDF
        text = self._extract_text(file_path)
        if not text:
            logger.warning(f"No text extracted from PDF: {file_path}")
            return KnowledgeStore() # Return empty store if no text
        logger.debug(f"Extracted text (first 300 chars): {text[:300]}...")
        
        # Extract entities and relationships using NLTK methods + regex
        extracted_entities = self._extract_entities(text)
        logger.debug(f"Extracted {len(extracted_entities)} potential entities.")
        extracted_relationships = self._extract_relationships(text, extracted_entities)
        logger.debug(f"Generated {len(extracted_relationships)} potential relationships.")
        
        # Create knowledge store
        store = KnowledgeStore()
        entity_map: Dict[str, Entity] = {} # Map extracted entity text to store Entity object
        
        # Add entities to store
        logger.debug("Adding extracted entities to KnowledgeStore...")
        entity_add_count = 0
        for i, entity_data in enumerate(extracted_entities):
            # Use a more robust ID generation if needed, e.g., hash of text+type
            entity_id = f"entity_{entity_add_count}" # Simple unique ID for this parse
            try:
                entity = Entity(
                    id=entity_id,
                    type=entity_data['type'],
                    properties={
                        "text": entity_data['text'],
                        "context": entity_data['context']
                    }
                )
                if store.add_entity(entity):
                    entity_add_count += 1
                    # Store mapping from original text to the entity object in the store
                    # Handle potential duplicate entity texts by storing the first one encountered
                    if entity_data['text'] not in entity_map:
                         entity_map[entity.properties['text']] = entity # Map using the actual text property
            except Exception as e:
                 logger.error(f"Failed to create or add entity from data {entity_data}: {e}")
        logger.info(f"Added {entity_add_count} unique entities to the store.")
        
        # Add relationships to store
        logger.debug("Adding generated relationships to KnowledgeStore...")
        rel_add_count = 0
        # # print(f"[DEBUG] entity_map keys: {list(entity_map.keys())}") # REMOVE DEBUG
        for i, rel_data in enumerate(extracted_relationships):
            # # print(f"[DEBUG] Processing rel_data: {rel_data}") # REMOVE DEBUG
            source_entity = entity_map.get(rel_data['source'])
            target_entity = entity_map.get(rel_data['target'])
            # # print(f"[DEBUG] Found source_entity: {source_entity.id if source_entity else None}, target_entity: {target_entity.id if target_entity else None}") # REMOVE DEBUG

            if source_entity and target_entity:
                 try:
                     relationship = Relationship(
                         # id=f"rel_{i}", # Remove ID assignment - KnowledgeStore handles keys
                         type=rel_data['type'],
                         source=source_entity.id, # Use the ID from the store Entity
                         target=target_entity.id, # Use the ID from the store Entity
                         properties={
                             "context": rel_data['context']
                         }
                     )
                     if store.add_relationship(relationship):
                          rel_add_count += 1
                     # # print(f"[DEBUG] Added relationship to store: {relationship.id} ({source_entity.id} -> {target_entity.id})") # REMOVE FAULTY DEBUG
                 except Exception as e:
                     logger.error(f"Failed to create or add relationship from data {rel_data}: {e}")
            else:
                 # Log warning or handle cases where source/target entity wasn't found in map
                 logger.warning(f"Could not map source '{rel_data['source']}' or target '{rel_data['target']}' to entities for relationship.")
        
        logger.info(f"Added {rel_add_count} unique relationships to the store.")
        return store 