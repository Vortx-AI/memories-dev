import sys
import os
from pathlib import Path
import torch
from typing import Dict, Any, List, Optional, Tuple, Union
from dotenv import load_dotenv
import logging
import tempfile
import gc
import uuid
import json
from datetime import datetime

from memories.models.base_model import BaseModel
from memories.models.api_connector import get_connector

# Load environment variables
load_dotenv()

class LoadModel:
    def __init__(self, 
                 use_gpu: bool = True,
                 model_provider: str = None,
                 deployment_type: str = None,  # "local" or "api"
                 model_name: str = None,
                 api_key: str = None,
                 endpoint: str = None,  # Add endpoint parameter
                 device: str = None):
        """
        Initialize model loader with configuration.
        
        Args:
            use_gpu (bool): Whether to use GPU if available
            model_provider (str): The model provider (e.g., "deepseek", "azure-ai", "mistral")
            deployment_type (str): Either "local" or "api"
            model_name (str): Short name of the model from BaseModel.MODEL_MAPPINGS
            api_key (str): API key for the model provider (required for API deployment type)
            endpoint (str): Endpoint URL for the model provider (optional)
            device (str): Specific GPU device to use (e.g., "cuda:0", "cuda:1")
        """
        # Setup logging
        self.instance_id = str(uuid.uuid4())
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Set default values from config if not provided
        if not all([model_provider, deployment_type, model_name]):
            default_model = self.config["default_model"]
            default_config = self.config["models"][default_model]
            model_provider = model_provider or default_config["provider"]
            deployment_type = deployment_type or default_config["type"]
            model_name = model_name or default_model
        
        # Validate inputs
        if deployment_type not in self.config["deployment_types"]:
            raise ValueError(f"deployment_type must be one of: {self.config['deployment_types']}")
            
        # Special handling for azure-ai provider
        if model_provider == "azure-ai":
            if not endpoint:
                raise ValueError("endpoint is required for azure-ai provider")
        elif model_provider not in self.config["supported_providers"]:
            raise ValueError(f"model_provider must be one of: {self.config['supported_providers']}")
            
        if deployment_type == "api" and not api_key:
            raise ValueError("api_key is required for API deployment type")
        
        # Store configuration
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.model_provider = model_provider
        self.deployment_type = deployment_type
        self.model_name = model_name
        self.api_key = api_key
        self.endpoint = endpoint
        
        # Handle device selection
        self.device = device
        if self.use_gpu:
            if device:
                if not device.startswith("cuda:"):
                    raise ValueError("Device must be in format 'cuda:N' where N is the GPU index")
                device_idx = int(device.split(":")[-1])
                if device_idx >= torch.cuda.device_count():
                    raise ValueError(f"Device {device} not available. Maximum device index is {torch.cuda.device_count()-1}")
            else:
                self.device = "cuda:0"  # Default to first GPU
        else:
            self.device = "cpu"
            
        # Initialize appropriate model interface
        if deployment_type == "local":
            self.base_model = BaseModel.get_instance()
            success = self.base_model.initialize_model(
                model=model_name,
                use_gpu=use_gpu,
                device=device
            )
            if not success:
                raise RuntimeError(f"Failed to initialize model: {model_name}")
        else:  # api
            self.api_connector = get_connector(model_provider, api_key, endpoint)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration."""
        try:
            config_path = Path(__file__).parent / "config" / "model_config.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def get_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a response using either local model or API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters including:
                max_length: Maximum length of generated response
                temperature: Sampling temperature (0.0 to 1.0)
                top_p: Nucleus sampling parameter
                top_k: Top-k sampling parameter
                num_beams: Number of beams for beam search
                
        Returns:
            Dict[str, Any]: Response dictionary containing:
                text: The generated response text
                metadata: Generation metadata (tokens, time, etc)
                error: Error message if generation failed
        """
        if not prompt or not isinstance(prompt, str):
            return {
                "error": "Invalid prompt - must be non-empty string",
                "text": None,
                "metadata": None
            }
            
        try:
            # Log generation attempt
            self.logger.info(f"Generating response for prompt: {prompt[:100]}...")
            self.logger.debug(f"Full prompt: {prompt}")
            self.logger.info(f"Using deployment type: {self.deployment_type}")
            self.logger.debug(f"Generation parameters: {kwargs}")
            
            # Validate and set default parameters
            max_retries = kwargs.pop('max_retries', 3)
            timeout = kwargs.pop('timeout', 30)
            
            # Initialize response
            response = None
            error = None
            metadata = {
                "attempt": 0,
                "total_tokens": 0,
                "generation_time": 0
            }
            
            # Try generation with retries
            for attempt in range(max_retries):
                metadata["attempt"] = attempt + 1
                
                try:
                    if self.deployment_type == "local":
                        self.logger.info("Using base model for generation")
                        response = self.base_model.generate(
                            prompt,
                            timeout=timeout,
                            **kwargs
                        )
                    else:
                        self.logger.info(f"Using {self.model_provider} API connector")
                        response = self.api_connector.generate(
                            prompt,
                            timeout=timeout,
                            **kwargs
                        )
                        
                    if response:
                        break
                        
                except Exception as e:
                    error = str(e)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {error}",
                        exc_info=True
                    )
                    if attempt < max_retries - 1:
                        continue
            
            # Process results
            if response:
                # Extract metadata if available
                if isinstance(response, dict):
                    metadata.update(response.get('metadata', {}))
                    response = response.get('text', response)
                    
                self.logger.info(
                    f"Response generated successfully. Length: {len(response)}"
                )
                
                return {
                    "text": response,
                    "metadata": metadata,
                    "error": None
                }
            else:
                error_msg = error or "Failed to generate response after retries"
                self.logger.error(error_msg)
                return {
                    "text": None,
                    "metadata": metadata,
                    "error": error_msg
                }
                
        except Exception as e:
            self.logger.error(
                f"Unexpected error in get_response: {str(e)}",
                exc_info=True
            )
            return {
                "text": None,
                "metadata": {"attempt": 1},
                "error": f"Unexpected error: {str(e)}"
            }
    
    def cleanup(self):
        """Clean up model resources."""
        if self.deployment_type == "local" and hasattr(self, 'base_model'):
            self.base_model.cleanup()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        self.logger.info("Model resources cleaned up")

    def get_response_with_context(self, prompt: str, context_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate a response using context-aware prompting.
        
        Args:
            prompt: The input prompt
            context_data: Dictionary containing contextual information including:
                - location_info: Location details
                - raw_data_summary: Summary of raw data from different sources
                - analysis_results: Results of various analyses
                - scenario_projections: Future scenario projections
                - historical_trends: Historical trend analysis
            **kwargs: Additional generation parameters including:
                max_length: Maximum length of generated response
                temperature: Sampling temperature (0.0 to 1.0)
                top_p: Nucleus sampling parameter
                top_k: Top-k sampling parameter
                num_beams: Number of beams for beam search
                
        Returns:
            Dict[str, Any]: Response dictionary containing:
                text: The generated response text
                metadata: Generation metadata including context usage
                error: Error message if generation failed
        """
        if not prompt or not isinstance(prompt, str):
            return {
                "error": "Invalid prompt - must be non-empty string",
                "text": None,
                "metadata": None
            }
            
        if not context_data or not isinstance(context_data, dict):
            return {
                "error": "Invalid context_data - must be non-empty dictionary",
                "text": None,
                "metadata": None
            }
            
        try:
            # Log generation attempt with context
            self.logger.info(f"Generating context-aware response for prompt: {prompt[:100]}...")
            self.logger.debug(f"Full prompt: {prompt}")
            self.logger.debug(f"Context data keys: {list(context_data.keys())}")
            self.logger.info(f"Using deployment type: {self.deployment_type}")
            
            # Format prompt with context
            formatted_prompt = self._format_prompt_with_context(prompt, context_data)
            self.logger.debug(f"Formatted prompt with context: {formatted_prompt[:200]}...")
            
            # Get response using formatted prompt
            response = self.get_response(formatted_prompt, **kwargs)
            
            if response.get("error"):
                return response
                
            # Analyze context usage in response
            context_usage = self._analyze_context_usage(response["text"], context_data)
            
            # Update metadata with context usage
            response["metadata"]["context_used"] = context_usage
            response["metadata"]["context_keys"] = list(context_data.keys())
            response["metadata"]["prompt_length"] = len(formatted_prompt)
            response["metadata"]["context_integration_timestamp"] = datetime.now().isoformat()
            
            return response
            
        except Exception as e:
            self.logger.error(
                f"Unexpected error in get_response_with_context: {str(e)}",
                exc_info=True
            )
            return {
                "text": None,
                "metadata": {"attempt": 1},
                "error": f"Error processing context: {str(e)}"
            }
            
    def _format_prompt_with_context(self, prompt: str, context_data: Dict[str, Any]) -> str:
        """Format the prompt by incorporating context data."""
        context_sections = []
        
        # Add location information if available
        if "location_info" in context_data:
            loc = context_data["location_info"]
            context_sections.append(
                f"Location: {loc.get('name', 'Unknown')}\n"
                f"Type: {loc.get('type', 'Unknown')}\n"
                f"Area: {loc.get('area_sqkm', 0):.2f} km²"
            )
        
        # Add data summaries if available
        if "raw_data_summary" in context_data:
            data = context_data["raw_data_summary"]
            if "overture" in data:
                ov = data["overture"]
                context_sections.append(
                    f"Urban Data:\n"
                    f"- Buildings: {ov.get('total_buildings', 0)}\n"
                    f"- Places: {ov.get('total_places', 0)}\n"
                    f"- Transportation: {ov.get('total_transportation', 0)}"
                )
            if "sentinel" in data:
                sen = data["sentinel"]
                context_sections.append(
                    f"Satellite Data:\n"
                    f"- Scenes: {sen.get('total_scenes', 0)}\n"
                    f"- Coverage: {sen.get('coverage_percentage', 0)}%"
                )
        
        # Add analysis results if available
        if "analysis_results" in context_data:
            analysis = context_data["analysis_results"]
            if "urban_metrics" in analysis:
                um = analysis["urban_metrics"]
                context_sections.append(
                    f"Urban Analysis:\n"
                    f"- Building Density: {um.get('building_density', 0):.2f}/km²\n"
                    f"- Urbanization Level: {um.get('urbanization_level', 'Unknown')}"
                )
            if "environmental_metrics" in analysis:
                em = analysis["environmental_metrics"]
                context_sections.append(
                    f"Environmental Analysis:\n"
                    f"- Vegetation Index: {em.get('vegetation_index', 0)}\n"
                    f"- Environmental Health: {em.get('environmental_health', 'Unknown')}"
                )
        
        # Add scenario projections if available
        if "scenario_projections" in context_data:
            scenarios = context_data["scenario_projections"]
            context_sections.append("Future Scenarios:")
            for scenario_type, details in scenarios.items():
                context_sections.append(
                    f"{scenario_type.title()} Scenario (Probability: {details.get('probability', 0)*100:.0f}%):\n"
                    f"- Changes: {', '.join(str(c) for c in details.get('changes', []))}\n"
                    f"- Impact Factors: {', '.join(str(f) for f in details.get('impact_factors', []))}"
                )
        
        # Add historical trends if available
        if "historical_trends" in context_data:
            trends = context_data["historical_trends"]
            context_sections.append(
                f"Historical Trends:\n"
                f"- Growth Rate: {trends.get('growth_rate', 0):.2f}\n"
                f"- Trend Direction: {trends.get('trend_direction', 'stable')}\n"
                f"- Seasonal Factors: {', '.join(trends.get('seasonal_factors', []))}"
            )
        
        # Combine context sections with the original prompt
        context_text = "\n\n".join(context_sections)
        formatted_prompt = f"""Context Information:

{context_text}

User Query: {prompt}

Please provide a detailed response incorporating the above context."""
        
        return formatted_prompt
            
    def _analyze_context_usage(self, response: str, context_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze how different parts of the context were used in the response."""
        context_usage = {}
        response_lower = response.lower()
        
        for context_type, data in context_data.items():
            if isinstance(data, dict):
                # For nested dictionaries, check both keys and values
                key_terms = set()
                for k, v in data.items():
                    key_terms.add(str(k).lower())
                    if isinstance(v, (str, int, float)):
                        key_terms.add(str(v).lower())
                    elif isinstance(v, (list, tuple)):
                        key_terms.update(str(item).lower() for item in v)
                    elif isinstance(v, dict):
                        key_terms.update(str(k).lower() for k in v.keys())
                        key_terms.update(str(v).lower() for v in v.values() if isinstance(v, (str, int, float)))
            elif isinstance(data, (list, tuple)):
                key_terms = set(str(item).lower() for item in data)
            else:
                key_terms = set(str(data).lower().split())
            
            # Count how many key terms appear in response
            terms_found = sum(1 for term in key_terms if term in response_lower)
            if len(key_terms) > 0:
                usage_score = terms_found / len(key_terms)
            else:
                usage_score = 0.0
            
            context_usage[context_type] = usage_score
        
        return context_usage

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion response using either local model or API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Roles can be 'user', 'assistant', 'system', or 'function'.
            tools: Optional list of tool/function definitions that the model can use.
                  Each tool should have a 'type', 'function' with 'name', 'description', 'parameters'.
            tool_choice: How to handle tool selection. Options:
                - "auto": Let the model decide if it should call a function
                - "none": Don't call any functions
                - Dict with specific function to call
            **kwargs: Additional parameters including:
                temperature: Sampling temperature (0.0 to 1.0)
                max_tokens: Maximum tokens in the response
                top_p: Nucleus sampling parameter
                frequency_penalty: Frequency penalty parameter
                presence_penalty: Presence penalty parameter
                
        Returns:
            Dict[str, Any]: Response dictionary containing:
                message: The assistant's message
                tool_calls: List of tool calls if any
                metadata: Generation metadata
                error: Error message if generation failed
        """
        if not messages or not isinstance(messages, list):
            return {
                "error": "Invalid messages - must be non-empty list",
                "message": None,
                "tool_calls": None,
                "metadata": None
            }
            
        try:
            # Log generation attempt
            self.logger.info(f"Generating chat completion for {len(messages)} messages")
            self.logger.debug(f"Messages: {messages}")
            self.logger.debug(f"Tools available: {len(tools) if tools else 0}")
            
            # Validate and set default parameters
            max_retries = kwargs.pop('max_retries', 3)
            timeout = kwargs.pop('timeout', 30)
            
            # Initialize response
            response = None
            error = None
            metadata = {
                "attempt": 0,
                "total_tokens": 0,
                "generation_time": 0,
                "timestamp": datetime.now().isoformat()
            }
            
            # Try generation with retries
            for attempt in range(max_retries):
                metadata["attempt"] = attempt + 1
                
                try:
                    if self.deployment_type == "local":
                        self.logger.info("Using base model for chat completion")
                        response = self.base_model.chat_completion(
                            messages=messages,
                            tools=tools,
                            tool_choice=tool_choice,
                            timeout=timeout,
                            **kwargs
                        )
                    else:
                        self.logger.info(f"Using {self.model_provider} API connector")
                        response = self.api_connector.chat_completion(
                            messages=messages,
                            tools=tools,
                            tool_choice=tool_choice,
                            timeout=timeout,
                            **kwargs
                        )
                        
                    if response:
                        break
                        
                except Exception as e:
                    error = str(e)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {error}",
                        exc_info=True
                    )
                    if attempt < max_retries - 1:
                        continue
            
            # Process results
            if response:
                # Extract metadata if available
                if isinstance(response, dict):
                    metadata.update(response.get('metadata', {}))
                    
                self.logger.info("Chat completion generated successfully")
                
                return {
                    "message": response.get('message', {}),
                    "tool_calls": response.get('tool_calls', []),
                    "metadata": metadata,
                    "error": None
                }
            else:
                error_msg = error or "Failed to generate chat completion after retries"
                self.logger.error(error_msg)
                return {
                    "message": None,
                    "tool_calls": None,
                    "metadata": metadata,
                    "error": error_msg
                }
                
        except Exception as e:
            self.logger.error(
                f"Unexpected error in chat_completion: {str(e)}",
                exc_info=True
            )
            return {
                "message": None,
                "tool_calls": None,
                "metadata": {"attempt": 1},
                "error": f"Unexpected error: {str(e)}"
            }

    