from openai import OpenAI
import os
from typing import Optional

def query_ai(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """
    Query OpenAI's API with system and user prompts.
    
    Args:
        system_prompt (str): The system prompt to set context
        user_prompt (str): The user's input prompt
        json_mode (bool): Whether to request JSON formatted response
    
    Returns:
        str: The AI's response
    """
    # Initialize the client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create the completion
    completion = client.chat.completions.create(
        model="gpt-4",  # Note: "gpt-4o-mini" doesn't exist, using "gpt-4"
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"} if json_mode else None
    )
    
    # Return the response content or empty string if None
    return completion.choices[0].message.content or ""

# Example usage
if __name__ == "__main__":
    # Example system and user prompts
    system_prompt = "You are a helpful assistant."
    user_prompt = "What is the capital of France?"
    
    # Regular response
    response = query_ai(system_prompt, user_prompt)
    print("Regular response:", response)
    
    # JSON response
    json_response = query_ai(system_prompt, user_prompt, json_mode=True)
    print("JSON response:", json_response)
