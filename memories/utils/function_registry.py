"""
Function Registry containing function definitions and schemas.

This module serves as a central registry for all available functions in the system.
It provides schemas and metadata for each function, enabling dynamic function discovery
and validation. Each function is defined with its type, parameters, and requirements.
"""

FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "tokenize",
            "description": "Tokenize text into words using NLTK's TreebankWordTokenizer",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The input text to tokenize"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "segment_sentences",
            "description": "Split text into sentences using NLTK's PunktSentenceTokenizer",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The input text to split into sentences"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_location",
            "description": "Process location information and retrieve geometries",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_info": {
                        "type": "object",
                        "description": "Dictionary containing location, location_type, and coordinates",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Coordinate string"
                            },
                            "location_type": {
                                "type": "string",
                                "description": "Type of location (e.g., 'point')"
                            },
                            "coordinates": {
                                "type": "array",
                                "description": "(lat, lon) tuple",
                                "items": {
                                    "type": "number"
                                },
                                "minItems": 2,
                                "maxItems": 2
                            }
                        },
                        "required": ["location", "location_type", "coordinates"]
                    },
                    "radius_meters": {
                        "type": "number",
                        "description": "Search radius in meters",
                        "default": 1000
                    }
                },
                "required": ["location_info"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_spatial_relationships",
            "description": "Analyze spatial relationships between geometric features",
            "parameters": {
                "type": "object",
                "properties": {
                    "geometries": {
                        "type": "object",
                        "description": "Dictionary containing geometric features with a 'features' array",
                        "required": ["features"]
                    }
                },
                "required": ["geometries"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "format_response",
            "description": "Format data into a natural language response",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Original user query"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to format into a response"
                    }
                },
                "required": ["query", "data"]
            }
        }
    },
    {
        "type": "text",
        "name": "classify_query",
        "description": "Classifies the query and returns appropriate response based on classification (N: Direct model response, L0: Direct model response, L1_2: Extracted location information)",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user query to classify"},
                "load_model": {"type": "object", "description": "Initialized model instance"}
            },
            "required": ["query", "load_model"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_ndwi",
            "description": "Calculate Normalized Difference Water Index (NDWI) from multi-band image data",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Multi-band image data with shape (bands, height, width)"
                    },
                    "green_band": {
                        "type": "integer",
                        "description": "Index of the green band",
                        "default": 1
                    },
                    "nir_band": {
                        "type": "integer",
                        "description": "Index of the near-infrared band",
                        "default": 3
                    }
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_by_distance",
            "description": "Filter locations within a certain radius of a center point",
            "parameters": {
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "description": "List of locations to filter",
                        "items": {
                            "type": "object"
                        }
                    },
                    "center": {
                        "type": "array",
                        "description": "Center point coordinates [lat, lon]",
                        "items": {
                            "type": "number"
                        },
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Radius in kilometers"
                    }
                },
                "required": ["locations", "center", "radius_km"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_response",
            "description": "Generate a response using either local model or API",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The input prompt"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of generated response",
                        "optional": True
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature (0.0 to 1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "optional": True
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "earth",
        "name": "get_api_for_field",
        "description": "Determine which API to use for a specific field using FAISS similarity search",
        "parameters": {
            "type": "object",
            "properties": {
                "field": {"type": "string", "description": "The field name to match against stored values"}
            },
            "required": ["field"]
        }
    },
    {
        "type": "earth",
        "name": "query_field",
        "description": "Query a specific field using the appropriate API",
        "parameters": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "field": {"type": "string", "description": "Field name to query"}
            },
            "required": ["lat", "lon", "field"]
        }
    },
    {
        "type": "earth",
        "name": "get_location_data",
        "description": "Get data for multiple fields at a location",
        "parameters": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "required_fields": {"type": "array", "items": {"type": "string"}, "description": "List of field names to query"}
            },
            "required": ["lat", "lon", "required_fields"]
        }
    },
    {
        "type": "earth",
        "name": "determine_api",
        "description": "Determine which API to use based on context using FAISS similarity search",
        "parameters": {
            "type": "object",
            "properties": {
                "context": {"type": "string", "description": "The context string to match against stored values"}
            },
            "required": ["context"]
        }
    },
    {
        "type": "text",
        "name": "extract_query_info",
        "description": "Extract location information from the query using NLTK and model processing",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user's query"}
            },
            "required": ["query"]
        }
    },
    {
        "type": "context_utils",
        "name": "classify_query",
        "description": "Classifies the query and returns appropriate response based on classification (N: Direct model response, L0: Direct model response, L1_2: Extracted location information)",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user query to classify"},
                "load_model": {"type": "object", "description": "Initialized model instance"}
            },
            "required": ["query", "load_model"]
        }
    }
]

def get_function_schema(function_name: str) -> dict:
    """
    Get the schema for a specific function.
    
    Args:
        function_name: The name of the function to find
        
    Returns:
        The function schema dictionary or None if not found
    """
    for func in FUNCTIONS:
        if func["function"]["name"] == function_name:
            return func
    return None

def list_functions() -> list:
    """
    List all available functions.
    
    Returns:
        List of function names
    """
    return [func["function"]["name"] for func in FUNCTIONS] 