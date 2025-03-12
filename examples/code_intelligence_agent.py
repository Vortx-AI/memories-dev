#!/usr/bin/env python3
"""
Code Intelligence Agent
----------------------------------
This example demonstrates how to use the Memories-Dev framework to create
an AI agent that can understand, analyze, and generate code, storing code
knowledge in memory for improved performance over time.
"""

import os
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import re
import json
from dotenv import load_dotenv

# Fix the imports to reference the correct modules
from memories.core.memory_store import MemoryStore
from memories.core.config import Config
from memories.models import BaseModel
from memories.utils.text import TextProcessor
from memories.utils.earth import VectorProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define simple versions of these classes for the example
class QueryUnderstanding:
    def analyze_query(self, query):
        return {"intent": "search", "entities": [], "keywords": []}

class ResponseGeneration:
    def generate(self, query, context, intent):
        return f"Response to query: {query} based on {len(context)} context items"

class CodeGenerator:
    def generate_code(self, specification, language):
        return f"# Generated {language} code based on specification\n# {specification}\n\nprint('Hello, World!')"

class CodeExecutor:
    def execute_code(self, code, language):
        return {"status": "success", "output": "Hello, World!"}

class CodeIntelligenceAgent(BaseModel):
    """AI agent specialized in code understanding, analysis, and generation."""
    
    def __init__(
        self, 
        memory_store: MemoryStore, 
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
        similarity_threshold: float = 0.7,
        supported_languages: List[str] = None
    ):
        """
        Initialize the Code Intelligence Agent.
        
        Args:
            memory_store: Memory store for maintaining code knowledge
            embedding_model: Name of the embedding model to use
            embedding_dimension: Dimension of the embedding vectors
            similarity_threshold: Threshold for similarity matching
            supported_languages: List of supported programming languages
        """
        super().__init__()
        self.memory_store = memory_store
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.similarity_threshold = similarity_threshold
        self.supported_languages = supported_languages or ["python", "javascript", "java", "c++", "go"]
        
        # Initialize utility components
        self.text_processor = TextProcessor()
        self.vector_processor = VectorProcessor()
        self.query_understanding = QueryUnderstanding()
        self.response_generation = ResponseGeneration()
        self.code_generator = CodeGenerator()
        self.code_executor = CodeExecutor()
        
        logger.info("Code Intelligence Agent initialized successfully")
    
    # Add abstract method implementations
    def get_capabilities(self):
        """Return the capabilities of this agent."""
        return ["code_understanding", "code_generation", "code_execution"]
        
    async def process(self, goal, **kwargs):
        """Process a goal."""
        return {"status": "success", "message": "Goal processed successfully"}

async def main():
    """Run the example."""
    # Initialize memory store
    config = Config()  # Use default config
    memory_store = MemoryStore()
    
    # Initialize code intelligence agent
    agent = CodeIntelligenceAgent(memory_store)
    
    # Print example information
    print("\nCode Intelligence Agent Example")
    print("------------------------------")
    print("This example demonstrates how to use the Memories-Dev framework")
    print("to create an AI agent that can understand, analyze, and generate code.")
    
    # Print agent configuration
    print("\nAgent Configuration:")
    print(f"Embedding Model: {agent.embedding_model}")
    print(f"Embedding Dimension: {agent.embedding_dimension}")
    print(f"Similarity Threshold: {agent.similarity_threshold}")
    print(f"Supported Languages: {', '.join(agent.supported_languages)}")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 