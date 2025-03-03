"""
Query understanding module for handling query classification and location extraction.
"""

from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv
import os

from memories.utils.text.context_utils import classify_query
from memories.utils.text.nlp_utils import initialize_nltk,extract_location_entities
from memories.utils.earth.location_utils import normalize_location, is_valid_coordinates

from memories.models.load_model import LoadModel
from memories.models.model_base import BaseModel


# Load environment variables
load_dotenv()

class QueryUnderstanding(BaseModel):
    """Module for handling query understanding and classification."""
    
    def __init__(self, model: Optional[LoadModel] = None):
        """Initialize the Query Understanding module.
        
        Args:
            model (Optional[LoadModel]): Model instance for language processing
        """
        super().__init__(name="query_understanding", model=model)
        self.logger = logging.getLogger(__name__)
        initialize_nltk()
    
    def requires_model(self) -> bool:
        """This module requires a model for classification."""
        return True
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify the query and extract relevant information.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict containing classification and extracted information
        """
        try:
            # Get initial classification
            result = classify_query(query, self.model)
            
            # For location-based queries, extract additional information
            if result.get("classification") == "L1_2":
                # Extract location entities
                locations = extract_location_entities(query)
                
                if locations:
                    location = locations[0]  # Use first location found
                    # Normalize the location information
                    normalized = normalize_location(location["text"], location["type"])
                    
                    result.update({
                        "location_details": location,
                        "normalized_location": normalized
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in classify_query: {str(e)}")
            return {
                "error": str(e),
                "classification": None,
                "response": f"Error: {str(e)}"
            }

class LocationExtractor(BaseModel):
    """Module for extracting and processing location information."""
    
    def __init__(self, model: Optional[LoadModel] = None):
        """Initialize the Location Extractor.
        
        Args:
            model (Optional[LoadModel]): Model instance for processing
        """
        super().__init__(name="location_extractor", model=model)
        self.logger = logging.getLogger(__name__)
        initialize_nltk()
    
    def requires_model(self) -> bool:
        """This module requires a model for processing."""
        return True
    
    def extract_query_info(self, query: str) -> Dict[str, Any]:
        """
        Extract location information from the query.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict containing extracted location information
        """
        try:
            # First check for coordinates
            if is_valid_coordinates(query):
                return {
                    "data_type": "coordinates",
                    "location_info": {
                        "location": query,
                        "location_type": "point"
                    }
                }
            
            # Extract location entities
            locations = extract_location_entities(query)
            
            if locations:
                location = locations[0]  # Use first location found
                return {
                    "data_type": "text",
                    "location_info": {
                        "location": location["text"],
                        "location_type": location["type"]
                    }
                }
            
            return {
                "data_type": "unknown",
                "location_info": None
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting query info: {str(e)}")
            return {
                "error": str(e),
                "data_type": "error"
            } 