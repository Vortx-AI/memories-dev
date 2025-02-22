import os
import sys
from typing import Dict, Any, Optional, List, Union, Literal
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import gc
import logging
from datetime import datetime
from langchain.llms.base import LLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import BaseModel, Field
import tempfile
import requests
from urllib.parse import quote
from core.memories.agent_capabilities import AGENT_CAPABILITIES
from .agentic_tool import AgenticTools, APIResponse
import nltk
import re
from memories.models.load_model import LoadModel

# Load environment variables
load_dotenv()

class DeepSeekLLM(LLM, BaseModel):
    model_name: str = Field(default="deepseek-ai/deepseek-coder-1.3b-base")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    top_p: float = Field(default=0.95)
    verbose: bool = Field(default=False)
    tokenizer: Any = Field(default=None)
    model: Any = Field(default=None)
    logger: Any = Field(default=None)
    offload_folder: str = Field(default=None)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_logging()
        self._initialize_model()
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO if self.verbose else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _initialize_model(self):
        if self.offload_folder is None:
            self.offload_folder = tempfile.mkdtemp()
            
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        if torch.cuda.is_available():
            dtype = torch.float16
            device_map = {
                "": torch.cuda.current_device()
            }
        else:
            dtype = torch.float32
            device_map = "cpu"
            
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=dtype,
            device_map=device_map,
            low_cpu_mem_usage=True,
            offload_folder=self.offload_folder
        )
    
    def _cleanup(self):
        try:
            gc.collect()
            if torch.cuda.is_available():
                with torch.cuda.device('cuda'):
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {str(e)}")
            
    @property
    def _llm_type(self) -> str:
        return "deepseek"
        
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        try:
            self._cleanup()
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(prompt):].strip()
            
            self._cleanup()
            return response
            
        except Exception as e:
            self.logger.error(f"Error during generation: {str(e)}")
            self._cleanup()
            raise

class LocationInfo:
    def __init__(self):
        self.tools = AgenticTools()
        self.logger = logging.getLogger(__name__)
    
    def get_address_from_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get address details from coordinates."""
        response = self.tools.reverse_geocode(lat, lon)
        return response.data if response.status == "success" else {"error": response.error}
    
    def get_coords_from_address(self, address: str) -> Dict[str, Any]:
        """Get coordinates and details from address."""
        response = self.tools.forward_geocode(address)
        return response.data if response.status == "success" else {"error": response.error}

class InformationExtractor:
    def __init__(self, model: str = None):
        """Initialize the Information Extraction system with NLTK.
        
        Args:
            model (str, optional): Not used, kept for backward compatibility. Defaults to None.
        """
        # Initialize NLTK resources
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
        except Exception as e:
            self.logger.error(f"Error downloading NLTK data: {str(e)}")
        
        self.logger = logging.getLogger(__name__)
        self.location_info = LocationInfo()

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process the query to extract location and context information."""
        try:
            # Extract coordinates or location name
            location_info = self.extract_location_info(query)
            
            # Extract query terms for nearby searches
            query_term = None
            if any(keyword in query.lower() for keyword in ["near", "nearby", "around"]):
                for category, terms in AGENT_CAPABILITIES["query_terms"].items():
                    for term in terms:
                        if term in query.lower():
                            query_term = {
                                "category": category,
                                "term": term
                            }
                            break
                    if query_term:
                        break
            
            return {
                "location": location_info,
                "query_term": query_term,
                "original_query": query
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "query": query
            }

    def extract_location_info(self, query: str) -> Dict[str, Any]:
        """Extract location information from query using NLTK."""
        # First check for coordinates
        coordinates_pattern = r'\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?'
        coord_match = re.search(coordinates_pattern, query)
        if coord_match:
            lat, lon = map(float, coord_match.groups())
            return {
                "location": f"{lat}, {lon}",
                "location_type": "point",
                "coordinates": (lat, lon)
            }
        
        # Process with NLTK for named entities
        tokens = nltk.word_tokenize(query)
        pos_tags = nltk.pos_tag(tokens)
        named_entities = nltk.ne_chunk(pos_tags)
        
        # Look for location entities
        locations = []
        for entity in named_entities:
            if hasattr(entity, 'label'):
                if entity.label() in ["GPE", "LOCATION", "FACILITY"]:
                    location_text = ' '.join([leaf[0] for leaf in entity.leaves()])
                    locations.append((location_text, entity.label()))
        
        if locations:
            # Get the first location found
            location_text, label = locations[0]
            
            # Determine location type based on entity label
            location_type = "unknown"
            if label == "GPE":
                words = query.lower().split()
                if "state" in words or "province" in words:
                    location_type = "state"
                elif len(location_text.split()) == 1:
                    location_type = "city"
                else:
                    location_type = "address"
            elif label == "LOCATION":
                location_type = "point"
            elif label == "FACILITY":
                location_type = "address"
            
            return {
                "location": location_text,
                "location_type": location_type,
                "coordinates": None
            }
        
        return {
            "location": "",
            "location_type": "",
            "coordinates": None
        }

QueryClass = Literal["N", "L0", "L1_2"]

def classify_query(query: str, load_model: Any) -> Dict[str, Union[str, Dict]]:
    """
    Classifies the query and returns appropriate response based on classification:
    N: Direct model response
    L0: Direct model response
    L1_2: Extracted location information
    
    Args:
        query (str): The user query to classify
        load_model (Any): Initialized model instance
    
    Returns:
        Dict containing classification and either response or location info
    """
    
    # First, classify the query
    classification_prompt = f"""Analyze the following query and classify it into one of these categories:
    N: Query has NO location component and can be answered by any AI model
    L0: Query HAS location component but can still be answered without additional data
    L1_2: Query HAS location component and NEEDS additional geographic data

    Examples:
    "What is the capital of France?" -> L0 (has location but needs no additional data)
    "What restaurants are near me?" -> L1_2 (needs actual location data)
    "How do I write a Python function?" -> N (no location component)
    "Tell me about Central Park" -> L0 (has location but needs no additional data)
    "Find cafes within 2km of Times Square" -> L1_2 (needs additional geographic data)
    
    Query to classify: "{query}"
    
    Return only one of these labels: N, L0, or L1_2
    """
    
    # Get classification from the model
    response = load_model.get_response(classification_prompt).strip()
    
    # Validate and clean response
    valid_classes = {"N", "L0", "L1_2"}
    response = response.upper()
    
    # Extract classification
    classification = "N"  # default
    for valid_class in valid_classes:
        if valid_class in response:
            classification = valid_class
            break
    
    # Handle response based on classification
    if classification in ["N", "L0"]:
        # For N and L0, get direct response from model
        answer_prompt = f"""Please provide a clear and concise answer to the following query:
        
        Query: {query}
        
        Provide only the answer without any additional context or prefixes."""
        
        model_response = load_model.get_response(answer_prompt).strip()
        
        return {
            "classification": classification,
            "response": model_response
        }
    
    else:  # L1_2
        # For L1_2, extract location information
        location_prompt = f"""From the following query, extract only the location information. 
        If coordinates are present, return them. If named locations are present, return them.
        If relative locations (like "near me") are present, indicate that user location is needed.

        Query: {query}
        
        Return only the location information without any additional explanation."""
        
        location_info = load_model.get_response(location_prompt).strip()
        
        return {
            "classification": classification,
            "location_info": location_info
        }

class LocationExtractor:
    def __init__(self, load_model: Any):
        """
        Initialize the Location Extractor.
        
        Args:
            load_model (Any): The initialized model instance
        """
        self.load_model = load_model

    def extract_query_info(self, query: str) -> Dict[str, Any]:
        """
        Extract data type and location information from a query.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict containing data type and location information
        """
        try:
            # Extract data type being requested
            data_type_prompt = f"""From the following query, what type of data or information is being requested?
            Examples:
            "Find restaurants near Central Park" -> restaurants
            "What is the weather in London?" -> weather
            "Show me hotels within 5km of the Eiffel Tower" -> hotels
            "What is the population density in Manhattan?" -> population density
            
            Query: {query}
            
            Return only the type of data/information being requested, as a single word or short phrase."""
            
            data_type = self.load_model.get_response(data_type_prompt).strip()
            
            # Extract location and its type
            location_prompt = f"""From the following query, extract:
            1. The location mentioned
            2. The type of location (coordinates, address, landmark, city, state, country, etc.)
            
            Examples:
            "Find cafes near 40.7128, -74.0060" -> Location: 40.7128, -74.0060 | Type: coordinates
            "Show restaurants in Manhattan" -> Location: Manhattan | Type: city district
            "What's the weather at the Eiffel Tower?" -> Location: Eiffel Tower | Type: landmark
            
            Query: {query}
            
            Return in format: Location: <location> | Type: <type>"""
            
            location_info = self.load_model.get_response(location_prompt).strip()
            
            # Parse location response
            try:
                location_parts = location_info.split("|")
                location = location_parts[0].replace("Location:", "").strip()
                location_type = location_parts[1].replace("Type:", "").strip()
            except:
                location = location_info
                location_type = "unknown"
            
            return {
                "data_type": data_type,
                "location_info": {
                    "location": location,
                    "location_type": location_type
                }
            }
            
        except Exception as e:
            return {
                "error": f"Error extracting information: {str(e)}",
                "data_type": None,
                "location_info": None
            }

    def is_valid_coordinates(self, location: str) -> bool:
        """
        Check if the location string contains valid coordinates.
        
        Args:
            location (str): The location string to check
            
        Returns:
            bool: True if valid coordinates, False otherwise
        """
        try:
            # Remove any whitespace and split by comma
            parts = location.replace(" ", "").split(",")
            if len(parts) != 2:
                return False
                
            # Try to convert to float
            lat, lon = float(parts[0]), float(parts[1])
            
            # Check if within valid range
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except:
            return False

    def normalize_location(self, location: str, location_type: str) -> Dict[str, Any]:
        """
        Normalize the location information based on its type.
        
        Args:
            location (str): The location string
            location_type (str): The type of location
            
        Returns:
            Dict containing normalized location information
        """
        try:
            normalized = {
                "original": location,
                "type": location_type.lower(),
                "coordinates": None
            }
            
            # If it's already coordinates, validate and format
            if location_type.lower() == "coordinates":
                if self.is_valid_coordinates(location):
                    lat, lon = map(float, location.replace(" ", "").split(","))
                    normalized["coordinates"] = {"lat": lat, "lon": lon}
            
            return normalized
            
        except Exception as e:
            return {
                "error": f"Error normalizing location: {str(e)}",
                "original": location,
                "type": location_type,
                "coordinates": None
            }

def main():
    """Test the LocationExtractor"""
    # Initialize the model
    load_model = LoadModel(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    # Initialize the extractor
    extractor = LocationExtractor(load_model)
    
    # Test queries
    test_queries = [
        "Find restaurants near Central Park",
        "What's the weather at 40.7128, -74.0060",
        "Show me hotels in Manhattan",
        "What's the population density of New York City"
    ]
    
    # Test extraction
    for query in test_queries:
        print("\n" + "="*50)
        print(f"Query: {query}")
        result = extractor.extract_query_info(query)
        print("\nExtracted Information:")
        print(f"Data Type: {result.get('data_type')}")
        if result.get('location_info'):
            loc_info = result['location_info']
            print(f"Location: {loc_info.get('location')}")
            print(f"Location Type: {loc_info.get('location_type')}")
            
            # Test normalization
            normalized = extractor.normalize_location(
                loc_info.get('location'),
                loc_info.get('location_type')
            )
            print("\nNormalized Location:")
            print(normalized)

if __name__ == "__main__":
    main()
