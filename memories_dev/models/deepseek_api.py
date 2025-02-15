from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from typing import Optional
import json

class DeepseekAPI:
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-1.3b-base", use_gpu: bool = True):
        """
        Initialize the Deepseek model.
        
        Args:
            model_name (str): Name of the Deepseek model to use
            use_gpu (bool): Whether to use GPU if available
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            low_cpu_mem_usage=True
        )
        self.model.to(self.device)

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

def query_ai(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """
    Query Deepseek model with system and user prompts.
    
    Args:
        system_prompt (str): The system prompt to set context
        user_prompt (str): The user's input prompt
        json_mode (bool): Whether to request JSON formatted response
    
    Returns:
        str: The AI's response
    """
    # Initialize the client
    client = DeepseekAPI()
    
    try:
        # Format the prompt
        if json_mode:
            formatted_prompt = f"""
            {system_prompt}
            Please provide your response in valid JSON format.
            User: {user_prompt}
            Assistant: """
        else:
            formatted_prompt = f"""
            {system_prompt}
            User: {user_prompt}
            Assistant: """

        # Tokenize input
        inputs = client.tokenizer(formatted_prompt, return_tensors="pt").to(client.device)
        
        # Generate response
        with torch.no_grad():
            outputs = client.model.generate(
                **inputs,
                max_length=2048,
                temperature=0.7,
                pad_token_id=client.tokenizer.eos_token_id,
                do_sample=True,
                top_p=0.95
            )
        
        # Decode response
        response = client.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the Assistant's response
        response = response.split("Assistant:")[-1].strip()
        
        # If JSON mode, validate JSON
        if json_mode:
            try:
                # Parse and re-serialize to ensure valid JSON
                response = json.dumps(json.loads(response))
            except json.JSONDecodeError:
                response = json.dumps({"error": "Failed to generate valid JSON", "text": response})
        
        return response
    
    finally:
        # Cleanup resources
        client.cleanup()

# Example usage
if __name__ == "__main__":
    # Example system and user prompts
    system_prompt = "You are a helpful coding assistant."
    user_prompt = "Write a Python function to calculate factorial"
    
    # Regular response
    response = query_ai(system_prompt, user_prompt)
    print("Regular response:", response)
    
    # JSON response
    json_response = query_ai(system_prompt, user_prompt, json_mode=True)
    print("JSON response:", json_response)
