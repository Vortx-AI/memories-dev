import os
import sys
from typing import Dict, Any, Optional, List, Union
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
        """Initialize the Information Extraction system with LangChain and DeepSeek.
        
        Args:
            model (str, optional): The model to use for information extraction. Defaults to None.
        """
        offload_folder = os.path.join(
            tempfile.gettempdir(),
            'deepseek_offload'
        )
        os.makedirs(offload_folder, exist_ok=True)
        
        self.llm = DeepSeekLLM(
            model_name=model or os.getenv("DEEPEEKS_MODEL_NAME", "deepseek-ai/deepseek-coder-1.3b-base"),
            temperature=0.7,
            max_tokens=150,
            top_p=0.95,
            verbose=True,
            offload_folder=offload_folder
        )
        
        self.location_prompt = PromptTemplate(
            input_variables=["query"],
            template="""Given the query: '{query}'
If the query contains coordinates (numbers separated by comma), return those exact coordinates.
Otherwise, extract the location name.
Return ONLY the location without any additional text.
Location:"""
        )
        
        self.context_prompt = PromptTemplate(
            input_variables=["query"],
            template="""Given the query: '{query}'
Extract and return ONLY the type of information being requested (like area, population, weather, etc).
If asking about what is at a location, return 'location details'.
Information type:"""
        )
        
        self.geocode_prompt = PromptTemplate(
            input_variables=["address", "api_response"],
            template="""Given this address: '{address}' and the API response: {api_response}
Extract ONLY the latitude and longitude values.
Format the response exactly as 'lat, lon' (just the numbers).
Coordinates:"""
        )
        
        self.reverse_geocode_prompt = PromptTemplate(
            input_variables=["coordinates", "api_response"],
            template="""Given these coordinates: '{coordinates}' and the API response: {api_response}
Extract ONLY the complete address from the display_name field.
Return just the address text, nothing else.
Address:"""
        )
        
        self.location_chain = LLMChain(llm=self.llm, prompt=self.location_prompt)
        self.context_chain = LLMChain(llm=self.llm, prompt=self.context_prompt)
        self.geocode_chain = LLMChain(llm=self.llm, prompt=self.geocode_prompt)
        self.reverse_geocode_chain = LLMChain(llm=self.llm, prompt=self.reverse_geocode_prompt)
        self.location_info = LocationInfo()
        self.logger = logging.getLogger(__name__)

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
