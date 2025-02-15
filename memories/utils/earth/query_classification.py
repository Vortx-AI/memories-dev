from typing import Literal, Any, Dict, Union

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
    
    # Get classification from the model using the appropriate method
    # Assuming your LoadModel has a method like 'get_response' or 'predict'
    response = load_model.get_response(classification_prompt).strip()  # Update this line with your actual method
    
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
        
        model_response = load_model.get_response(answer_prompt).strip()  # Update this line with your actual method
        
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
        
        location_info = load_model.get_response(location_prompt).strip()  # Update this line with your actual method
        
        return {
            "classification": classification,
            "location_info": location_info
        }
