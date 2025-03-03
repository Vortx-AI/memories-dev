"""
Natural Language Processing utilities using NLTK.
"""

import nltk
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

def initialize_nltk():
    """Initialize required NLTK resources."""
    try:
        resources = [
            'punkt',
            'averaged_perceptron_tagger',
            'maxent_ne_chunker',
            'words'
        ]
        for resource in resources:
            nltk.download(resource, quiet=True)
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {str(e)}")
        raise

def extract_named_entities(text: str) -> List[Tuple[str, str]]:
    """
    Extract named entities from text using NLTK.
    
    Args:
        text (str): Input text to process
    
    Returns:
        List of tuples containing (entity_text, entity_type)
    """
    try:
        # Tokenize and tag the text
        tokens = nltk.word_tokenize(text)
        pos_tags = nltk.pos_tag(tokens)
        named_entities = nltk.ne_chunk(pos_tags)
        
        # Extract entities
        entities = []
        for entity in named_entities:
            if hasattr(entity, 'label'):
                entity_text = ' '.join([leaf[0] for leaf in entity.leaves()])
                entities.append((entity_text, entity.label()))
        
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting named entities: {str(e)}")
        return []

def extract_location_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extract location-related entities from text.
    
    Args:
        text (str): Input text to process
    
    Returns:
        List of dictionaries containing location information
    """
    try:
        entities = extract_named_entities(text)
        locations = []
        
        for entity_text, label in entities:
            if label in ["GPE", "LOCATION", "FACILITY"]:
                # Determine location type based on entity label and context
                location_type = "unknown"
                if label == "GPE":
                    words = text.lower().split()
                    if "state" in words or "province" in words:
                        location_type = "state"
                    elif len(entity_text.split()) == 1:
                        location_type = "city"
                    else:
                        location_type = "address"
                elif label == "LOCATION":
                    location_type = "point"
                elif label == "FACILITY":
                    location_type = "address"
                
                locations.append({
                    "text": entity_text,
                    "type": location_type,
                    "label": label
                })
        
        return locations
        
    except Exception as e:
        logger.error(f"Error extracting location entities: {str(e)}")
        return [] 