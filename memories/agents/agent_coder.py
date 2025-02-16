import os
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import gc
from langchain.llms.base import LLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import BaseModel, Field
import tempfile
import json
from pathlib import Path


# Load environment variables
load_dotenv()

def generate_code(query: str, available_fields: List[str]) -> str:
    """Generate Python code based on the query and available fields."""
    offload_folder = os.path.join(tempfile.gettempdir(), 'deepseek_offload')
    os.makedirs(offload_folder, exist_ok=True)
    
    llm = DeepSeekLLM(
        model_name=os.getenv("DEEPEEKS_MODEL_NAME", "deepseek-ai/deepseek-coder-1.3b-base"),
        temperature=0.7,
        max_tokens=150,
        top_p=0.95,
        verbose=True,
        offload_folder=offload_folder
    )
    
    prompt = PromptTemplate(
        input_variables=["user_query", "available_fields"],
        template="""write python code for {user_query} """
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        return chain.invoke({
            "user_query": query,
            "available_fields": ", ".join(available_fields)
        })["text"].strip()
    except Exception as e:
        logging.error(f"Error generating code: {str(e)}")
        return f"# Error: {str(e)}"

# Define DeepSeekLLM only once
class DeepSeekLLM(LLM, BaseModel):
    model_name: str = Field(default="deepseek-ai/deepseek-coder-1.3b-base")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=150)
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
            self.offload_folder = os.path.join(tempfile.gettempdir(), 'deepseek_offload')
        os.makedirs(self.offload_folder, exist_ok=True)
            
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
        run_manager: Optional[Any] = None,
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

class CodeGenerator:
    def __init__(self, offload_folder: Optional[str] = None):
        """Initialize the Code Generation system with API-based knowledge base."""
        if offload_folder is None:
            offload_folder = os.path.join(tempfile.gettempdir(), 'deepseek_offload')
        os.makedirs(offload_folder, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Load API knowledge base (using the provided APIs instead of a database)
        knowledge_path = os.path.join(os.getenv('PROJECT_ROOT', '.'), 'memories', 'agents', 'knowledge-base.json')
        try:
            with open(knowledge_path, 'r') as f:
                self.knowledge_base = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {str(e)}")
            raise
        
        self.llm = DeepSeekLLM(
            model_name=os.getenv("DEEPEEKS_MODEL_NAME", "deepseek-ai/deepseek-coder-1.3b-base"),
            temperature=0.7,
            max_tokens=2048,
            top_p=0.95,
            verbose=True,
            offload_folder=offload_folder
        )
        
        # Update prompt to instruct the LLM to generate code that calls the provided APIs.
        self.code_prompt = PromptTemplate(
            input_variables=["user_query", "knowledge_base"],
            template="""#Generate Python code to answer the following query using the provided API documentation.

#Query: {user_query}

#APIs and their details:
{knowledge_base}

#Your code should:
#1. Choose the most appropriate API based on the query.
#2. Construct proper HTTP requests using the API endpoints, methods, and parameters.
#3. Include necessary error handling and required imports.
#4. Follow best practices for Python coding.
#MUST not contain any text other than the code.Should not contain any comments or examples or expected outputs

#Generate only the Python code, with no additional explanation."""
        )
        
        self.code_chain = LLMChain(llm=self.llm, prompt=self.code_prompt)

    def process_query(self, query: str, memories: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Process a natural language query and generate appropriate code using the provided APIs.
        
        Args:
            query (str): Natural language query.
            memories (Dict[str, Any], optional): Additional memory data if applicable.
            
        Returns:
            Tuple[str, Dict[str, Any]]: Generated code and metadata.
        """
        try:
            # Format API knowledge for the prompt
            knowledge_str = json.dumps({
                "apis": self.knowledge_base.get("apis", []),
                "metadata": self.knowledge_base.get("metadata", {}),
                "memories": memories
            }, indent=2)
            
            # Generate code using the updated prompt
            response = self.code_chain.invoke({
                "user_query": query,
                "knowledge_base": knowledge_str
            })
            
            generated_code = response["text"].strip()
            
            # Return both the generated code and metadata
            #return generated_code, response
            return response["text"]
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return f"# Error: {str(e)}", {"error": str(e)}

    def _extract_used_functions(self, code: str) -> list:
        """Extract the names of knowledge base functions used in the generated code."""
        functions = []
        for func_name in self.knowledge_base["landuse"]["python_functions"].keys():
            if func_name in code:
                functions.append(func_name)
        return functions

    def generate_code(self, query: str) -> str:
        """
        Generate code based on the query (legacy method for compatibility).
        
        Args:
            query (str): Natural language query
            
        Returns:
            str: Generated Python code
        """
        code, _ = self.process_query(query)
        return code

class LocationExtractor:
    def __init__(self):
        """Initialize the Information Extraction system with NLTK."""
        offload_folder = os.path.join(
            tempfile.gettempdir(),
            'deepseek_offload'
        )
        os.makedirs(offload_folder, exist_ok=True)
        
        self.llm = DeepSeekLLM(
            model_name=os.getenv("DEEPEEKS_MODEL_NAME", "deepseek-ai/deepseek-coder-1.3b-base"),
            temperature=0.7,
            max_tokens=50,
            top_p=0.95,
            verbose=True,
            offload_folder=offload_folder
        )
        
        self.location_prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""Extract location information as a text string in the following format:
location: <place>, location_info: <type>

Types:
point = coordinates (12.345, 67.890)
city = city name
state = state name
country = country name
address = full address
polygon = area coordinates
unknown = no location found (use empty string)

Query: {user_query}
Response:"""
        )
        
        self.location_chain = LLMChain(llm=self.llm, prompt=self.location_prompt)
        self.logger = logging.getLogger(__name__)

    def process_query(self, user_query: str) -> str:
        """Process the query to extract location and information type."""
        try:
            location_response = self.location_chain.invoke({"user_query": user_query})["text"]
            return location_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return "location: , location_info: unknown"
            
        