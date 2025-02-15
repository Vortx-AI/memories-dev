import os
import logging
from typing import Dict, Any, Optional, List, Union
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

# Load environment variables
load_dotenv()

class DeepSeekLLM(LLM, BaseModel):
    model_name: str = Field(default="deepseek-ai/deepseek-coder-1.3b-base")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=150)  # Increased for longer responses
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
            device_map = { "": torch.cuda.current_device() }
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

class ResponseAgent:
    def __init__(self):
        """Initialize the Response Agent with LangChain and DeepSeek."""
        offload_folder = os.path.join(
            tempfile.gettempdir(),
            'deepseek_offload'
        )
        os.makedirs(offload_folder, exist_ok=True)
        
        self.llm = DeepSeekLLM(
            model_name=os.getenv("DEEPEEKS_MODEL_NAME", "deepseek-ai/deepseek-coder-1.3b-base"),
            temperature=0.7,
            max_tokens=250,  # Increased for more detailed responses
            top_p=0.95,
            verbose=True,
            offload_folder=offload_folder
        )
        
        self.response_prompt = PromptTemplate(
            input_variables=["query", "code_result"],
            template="""You are a helpful assistant having a conversation with a user. Respond to their query based on the data results in a friendly, natural way as if you're having a casual conversation.

User's Question: {query}

I found this data: {code_result}

Please respond in a conversational way that:
- Uses everyday language (avoid technical terms unless necessary)
- Explains the findings in a friendly, engaging manner
- Provides context and meaning behind the numbers
- Starts with phrases like "I found that...", "It looks like...", or "Based on the data..."
- Ends with a relevant observation or helpful note

If there's an error or no data:
- Apologize naturally
- Explain what went wrong in simple terms
- Suggest what might help

Remember to sound friendly and conversational, as if you're chatting with a friend!

Your conversational response:"""
        )
        
        self.response_chain = LLMChain(llm=self.llm, prompt=self.response_prompt)
        self.logger = logging.getLogger(__name__)

    def format_response(self, query: str, code_result: Any) -> str:
        """
        Format the code execution result into a conversational response.
        
        Args:
            query (str): Original user query
            code_result: Result from code execution
            
        Returns:
            str: Formatted conversational response
        """
        try:
            # Handle error cases
            if isinstance(code_result, str) and code_result.startswith('Error:'):
                return f"I apologize, but I encountered an error: {code_result}"
            
            if code_result is None:
                return "I couldn't find any matching data for your query."
            
            # Convert code_result to string if it's not already
            if not isinstance(code_result, str):
                code_result = str(code_result)
            
            # Generate response using LLM
            response = self.response_chain.invoke({
                "query": query,
                "code_result": code_result
            })["text"]
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error formatting response: {str(e)}")
            return f"I apologize, but I encountered an error while formatting the response: {str(e)}"
        