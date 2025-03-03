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
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import re
import json
from dotenv import load_dotenv

from memories import MemoryStore, Config
from memories.models import BaseModel
from memories.utils.text import TextProcessor
from memories.utils.earth import VectorProcessor
from memories.utils.code_generation import CodeGenerator
from memories.utils.code_execution import CodeExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
        super().__init__(name="code_intelligence_agent")
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
        self.vector_processor = VectorProcessor()
        self.code_generator = CodeGenerator()
        self.code_executor = CodeExecutor()
        
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.similarity_threshold = similarity_threshold
        self.supported_languages = supported_languages or ["python", "javascript", "java", "c++", "go"]
        
        # Initialize code knowledge cache
        self.code_knowledge_cache = {}
        
        logger.info(f"Code Intelligence Agent initialized with {embedding_model}")
        logger.info(f"Supported languages: {', '.join(self.supported_languages)}")
    
    async def store_code_snippet(self, code: str, language: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store a code snippet in memory.
        
        Args:
            code: Code snippet
            language: Programming language
            description: Description of what the code does
            metadata: Additional metadata
            
        Returns:
            Dictionary containing the stored code knowledge
        """
        # Validate language
        if language.lower() not in [lang.lower() for lang in self.supported_languages]:
            return {"error": f"Unsupported language: {language}"}
        
        # Process code and description
        processed_description = self.text_processor.preprocess(description)
        
        # Extract code features
        code_features = self._extract_code_features(code, language)
        
        # Generate embeddings
        code_embedding = self._generate_embedding(code)
        description_embedding = self._generate_embedding(processed_description)
        
        # Create combined embedding (weighted average)
        combined_embedding = self._combine_embeddings(
            [code_embedding, description_embedding],
            [0.6, 0.4]  # Weight code more than description
        )
        
        # Create code knowledge record
        code_knowledge = {
            "type": "code_snippet",
            "code": code,
            "language": language.lower(),
            "description": description,
            "code_features": code_features,
            "code_embedding": code_embedding,
            "description_embedding": description_embedding,
            "combined_embedding": combined_embedding,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in memory
        memory_id = self._store_in_memory(code_knowledge)
        code_knowledge["memory_id"] = memory_id
        
        # Update cache
        cache_key = hash(f"{code}_{language}_{description}") % 10000
        self.code_knowledge_cache[cache_key] = code_knowledge
        
        return code_knowledge
    
    async def search_code_knowledge(self, query: str, language: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for code knowledge similar to the query.
        
        Args:
            query: Query text to search for
            language: Optional filter by programming language
            top_k: Number of top results to return
            
        Returns:
            List of similar code snippets with similarity scores
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(self.text_processor.preprocess(query))
        
        # Retrieve all code knowledge
        all_code_knowledge = list(self.code_knowledge_cache.values())
        
        # Filter by language if specified
        if language:
            all_code_knowledge = [
                ck for ck in all_code_knowledge 
                if ck["language"].lower() == language.lower()
            ]
        
        # Calculate similarities
        similarities = []
        for ck in all_code_knowledge:
            # Compare with combined embedding
            similarity = self._calculate_similarity(query_embedding, ck["combined_embedding"])
            
            if similarity >= self.similarity_threshold:
                similarities.append({
                    "code_knowledge": ck,
                    "similarity": similarity
                })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Return top k results
        return similarities[:top_k]
    
    async def generate_code(self, prompt: str, language: str, context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate code based on a prompt and optional context.
        
        Args:
            prompt: Description of the code to generate
            language: Target programming language
            context: Optional context from previous code knowledge
            
        Returns:
            Generated code with metadata
        """
        # Validate language
        if language.lower() not in [lang.lower() for lang in self.supported_languages]:
            return {"error": f"Unsupported language: {language}"}
        
        # Prepare context for code generation
        generation_context = []
        if context:
            for item in context:
                code_knowledge = item["code_knowledge"]
                generation_context.append({
                    "code": code_knowledge["code"],
                    "language": code_knowledge["language"],
                    "description": code_knowledge["description"],
                    "relevance": item["similarity"]
                })
        
        # Generate code
        generated_code = self.code_generator.generate(
            prompt=prompt,
            language=language,
            context=generation_context
        )
        
        # Extract features from generated code
        code_features = self._extract_code_features(generated_code, language)
        
        # Create result
        result = {
            "prompt": prompt,
            "language": language,
            "generated_code": generated_code,
            "code_features": code_features,
            "context_used": len(generation_context) if context else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store the generated code in memory
        await self.store_code_snippet(
            code=generated_code,
            language=language,
            description=prompt,
            metadata={"generated": True, "context_used": len(generation_context) if context else 0}
        )
        
        return result
    
    async def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze code to extract insights and potential improvements.
        
        Args:
            code: Code to analyze
            language: Programming language of the code
            
        Returns:
            Analysis results
        """
        # Validate language
        if language.lower() not in [lang.lower() for lang in self.supported_languages]:
            return {"error": f"Unsupported language: {language}"}
        
        # Extract code features
        code_features = self._extract_code_features(code, language)
        
        # Calculate complexity metrics
        complexity = self._calculate_complexity(code, language)
        
        # Identify potential issues
        issues = self._identify_issues(code, language)
        
        # Search for similar code in memory for comparison
        code_embedding = self._generate_embedding(code)
        similar_code = []
        
        for ck in self.code_knowledge_cache.values():
            if ck["language"].lower() == language.lower():
                similarity = self._calculate_similarity(code_embedding, ck["code_embedding"])
                if similarity >= self.similarity_threshold and similarity < 0.98:  # Avoid near-duplicates
                    similar_code.append({
                        "code": ck["code"],
                        "description": ck["description"],
                        "similarity": similarity
                    })
        
        # Sort by similarity
        similar_code.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Create analysis result
        analysis = {
            "language": language,
            "code_features": code_features,
            "complexity": complexity,
            "issues": issues,
            "similar_code": similar_code[:3],  # Top 3 similar snippets
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    async def execute_code(self, code: str, language: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code and return the results.
        
        Args:
            code: Code to execute
            language: Programming language
            inputs: Optional inputs for the code
            
        Returns:
            Execution results
        """
        # Validate language (currently only Python is supported for execution)
        if language.lower() != "python":
            return {"error": f"Code execution is currently only supported for Python"}
        
        # Execute the code
        execution_result = self.code_executor.execute(
            code=code,
            inputs=inputs or {}
        )
        
        # Create result
        result = {
            "language": language,
            "execution_successful": execution_result.get("success", False),
            "output": execution_result.get("output", ""),
            "error": execution_result.get("error", ""),
            "execution_time": execution_result.get("execution_time", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _extract_code_features(self, code: str, language: str) -> Dict[str, Any]:
        """Extract features from code."""
        features = {
            "length": len(code),
            "line_count": len(code.split("\n")),
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        # Extract language-specific features
        if language.lower() == "python":
            # Extract functions
            function_pattern = r"def\s+(\w+)\s*\("
            features["functions"] = re.findall(function_pattern, code)
            
            # Extract classes
            class_pattern = r"class\s+(\w+)"
            features["classes"] = re.findall(class_pattern, code)
            
            # Extract imports
            import_pattern = r"import\s+(\w+)|from\s+(\w+)"
            imports = re.findall(import_pattern, code)
            features["imports"] = [imp[0] or imp[1] for imp in imports]
            
        elif language.lower() == "javascript":
            # Extract functions
            function_pattern = r"function\s+(\w+)|const\s+(\w+)\s*=\s*\([^)]*\)\s*=>"
            functions = re.findall(function_pattern, code)
            features["functions"] = [f[0] or f[1] for f in functions]
            
            # Extract classes
            class_pattern = r"class\s+(\w+)"
            features["classes"] = re.findall(class_pattern, code)
            
            # Extract imports
            import_pattern = r"import\s+.*?from\s+['\"](.+?)['\"]"
            features["imports"] = re.findall(import_pattern, code)
        
        return features
    
    def _calculate_complexity(self, code: str, language: str) -> Dict[str, float]:
        """Calculate code complexity metrics."""
        # Simple complexity metrics
        complexity = {
            "cyclomatic_complexity": 1,  # Base complexity
            "cognitive_complexity": 0
        }
        
        if language.lower() == "python":
            # Count control flow statements to estimate cyclomatic complexity
            control_flow_pattern = r"\s(if|for|while|elif|else|try|except|with)\s"
            control_flow_count = len(re.findall(control_flow_pattern, code))
            complexity["cyclomatic_complexity"] += control_flow_count
            
            # Estimate cognitive complexity
            nesting_level = 0
            for line in code.split("\n"):
                if re.search(r":\s*$", line) and re.search(r"\s(if|for|while|elif|with)", line):
                    nesting_level += 1
                    complexity["cognitive_complexity"] += nesting_level
                elif re.search(r"^\s*return", line) and nesting_level > 0:
                    nesting_level -= 1
        
        elif language.lower() == "javascript":
            # Count control flow statements
            control_flow_pattern = r"\s(if|for|while|else|try|catch|switch)\s"
            control_flow_count = len(re.findall(control_flow_pattern, code))
            complexity["cyclomatic_complexity"] += control_flow_count
            
            # Count curly braces to estimate nesting
            open_braces = code.count("{")
            close_braces = code.count("}")
            complexity["cognitive_complexity"] = abs(open_braces - close_braces) + control_flow_count
        
        return complexity
    
    def _identify_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Identify potential issues in the code."""
        issues = []
        
        if language.lower() == "python":
            # Check for common Python issues
            
            # Unused imports
            import_pattern = r"import\s+(\w+)|from\s+(\w+)"
            imports = re.findall(import_pattern, code)
            for imp in imports:
                import_name = imp[0] or imp[1]
                if import_name and import_name not in code.replace(f"import {import_name}", ""):
                    issues.append({
                        "type": "unused_import",
                        "description": f"Unused import: {import_name}",
                        "severity": "low"
                    })
            
            # Bare except clauses
            if re.search(r"except:", code):
                issues.append({
                    "type": "bare_except",
                    "description": "Bare except clause found. Consider catching specific exceptions.",
                    "severity": "medium"
                })
            
            # Long lines
            for i, line in enumerate(code.split("\n")):
                if len(line) > 100:
                    issues.append({
                        "type": "long_line",
                        "description": f"Line {i+1} is too long ({len(line)} characters)",
                        "severity": "low"
                    })
        
        elif language.lower() == "javascript":
            # Check for common JavaScript issues
            
            # Console.log statements
            console_logs = re.findall(r"console\.log", code)
            if console_logs:
                issues.append({
                    "type": "console_log",
                    "description": f"Found {len(console_logs)} console.log statements that should be removed in production",
                    "severity": "low"
                })
            
            # Var usage (prefer let/const)
            var_usage = re.findall(r"\bvar\s+", code)
            if var_usage:
                issues.append({
                    "type": "var_usage",
                    "description": f"Found {len(var_usage)} instances of 'var'. Consider using 'let' or 'const' instead.",
                    "severity": "medium"
                })
        
        return issues
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        # In a real implementation, this would use an embedding model
        # For demonstration, we'll generate a random vector
        
        # Use hash of text to ensure same text gets same embedding
        text_hash = hash(text)
        np.random.seed(text_hash)
        
        # Generate random embedding vector
        embedding = np.random.normal(0, 1, self.embedding_dimension)
        
        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def _combine_embeddings(self, embeddings: List[List[float]], weights: Optional[List[float]] = None) -> List[float]:
        """Combine multiple embeddings with optional weights."""
        if not embeddings:
            return []
        
        # Default to equal weights if not provided
        if not weights:
            weights = [1.0 / len(embeddings)] * len(embeddings)
        
        # Normalize weights to sum to 1
        weights = [w / sum(weights) for w in weights]
        
        # Convert to numpy arrays
        np_embeddings = [np.array(emb) for emb in embeddings]
        
        # Weighted average
        combined = sum(w * emb for w, emb in zip(weights, np_embeddings))
        
        # Normalize to unit length
        combined = combined / np.linalg.norm(combined)
        
        return combined.tolist()
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
    
    def _store_in_memory(self, record: Dict[str, Any], memory_type: str = "warm") -> str:
        """Store record in memory and return memory ID."""
        # Generate memory ID
        memory_id = f"code_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(record)) % 1000}"
        
        # Store in appropriate memory
        if memory_type == "hot":
            self.memory_store.hot_memory.store({
                "memory_id": memory_id,
                "record": record
            })
        elif memory_type == "warm":
            self.memory_store.warm_memory.store({
                "memory_id": memory_id,
                "record": record
            })
        else:  # "cold"
            self.memory_store.cold_memory.store({
                "memory_id": memory_id,
                "record": record
            })
        
        return memory_id

def simulate_code_snippets() -> List[Dict[str, Any]]:
    """Generate simulated code snippets for demonstration."""
    return [
        {
            "code": """
def fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
            """,
            "language": "python",
            "description": "Recursive function to calculate Fibonacci numbers",
            "metadata": {
                "category": "algorithms",
                "complexity": "recursive",
                "importance": 0.8
            }
        },
        {
            "code": """
def fibonacci_optimized(n):
    \"\"\"Calculate the nth Fibonacci number using dynamic programming.\"\"\"
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    fib = [0] * (n + 1)
    fib[1] = 1
    
    for i in range(2, n + 1):
        fib[i] = fib[i-1] + fib[i-2]
    
    return fib[n]
            """,
            "language": "python",
            "description": "Optimized function to calculate Fibonacci numbers using dynamic programming",
            "metadata": {
                "category": "algorithms",
                "complexity": "iterative",
                "importance": 0.85
            }
        },
        {
            "code": """
import numpy as np
import matplotlib.pyplot as plt

def plot_data(x, y, title="Data Plot", xlabel="X", ylabel="Y"):
    \"\"\"Plot data using matplotlib.\"\"\"
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, 'o-', linewidth=2)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
            """,
            "language": "python",
            "description": "Function to plot data using matplotlib",
            "metadata": {
                "category": "data_visualization",
                "complexity": "simple",
                "importance": 0.75
            }
        },
        {
            "code": """
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

def insert_into_bst(root, value):
    \"\"\"Insert a value into a binary search tree.\"\"\"
    if root is None:
        return Node(value)
    
    if value < root.value:
        root.left = insert_into_bst(root.left, value)
    else:
        root.right = insert_into_bst(root.right, value)
    
    return root

def search_bst(root, value):
    \"\"\"Search for a value in a binary search tree.\"\"\"
    if root is None or root.value == value:
        return root
    
    if value < root.value:
        return search_bst(root.left, value)
    else:
        return search_bst(root.right, value)
            """,
            "language": "python",
            "description": "Binary search tree implementation with insert and search operations",
            "metadata": {
                "category": "data_structures",
                "complexity": "medium",
                "importance": 0.9
            }
        },
        {
            "code": """
function debounce(func, wait) {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Usage example
const debouncedSearch = debounce(function(searchTerm) {
  console.log('Searching for:', searchTerm);
  // Perform search operation
}, 300);

// Call this when input changes
document.querySelector('input').addEventListener('input', function(e) {
  debouncedSearch(e.target.value);
});
            """,
            "language": "javascript",
            "description": "Debounce function to limit the rate at which a function can fire",
            "metadata": {
                "category": "utility_functions",
                "complexity": "medium",
                "importance": 0.8
            }
        }
    ]

async def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./code_intelligence_data",
        hot_memory_size=50,
        warm_memory_size=500,
        cold_memory_size=5000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize code intelligence agent
    code_agent = CodeIntelligenceAgent(memory_store)
    
    # Load code snippets
    code_snippets = simulate_code_snippets()
    
    # Store code snippets
    logger.info("Storing code snippets in memory...")
    for snippet in code_snippets:
        await code_agent.store_code_snippet(
            code=snippet["code"],
            language=snippet["language"],
            description=snippet["description"],
            metadata=snippet["metadata"]
        )
    
    # Search for code knowledge
    query = "fibonacci implementation"
    logger.info(f"\nSearching for code related to: '{query}'")
    
    search_results = await code_agent.search_code_knowledge(query, top_k=2)
    
    logger.info("\nTop relevant code snippets:")
    for i, result in enumerate(search_results):
        code_knowledge = result["code_knowledge"]
        logger.info(f"{i+1}. Relevance: {result['similarity']:.4f}")
        logger.info(f"   Description: {code_knowledge['description']}")
        logger.info(f"   Language: {code_knowledge['language']}")
        logger.info(f"   Code snippet (first 3 lines):")
        code_lines = code_knowledge["code"].strip().split("\n")[:3]
        for line in code_lines:
            logger.info(f"      {line}")
        logger.info(f"      ...")
    
    # Generate code based on prompt and context
    prompt = "Create a function to calculate the nth Fibonacci number using memoization"
    logger.info(f"\nGenerating code for: '{prompt}'")
    
    generated_code = await code_agent.generate_code(
        prompt=prompt,
        language="python",
        context=search_results
    )
    
    logger.info("\nGenerated code:")
    logger.info(generated_code["generated_code"])
    logger.info(f"Context used: {generated_code['context_used']} snippets")
    
    # Analyze code
    code_to_analyze = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
        else:
            result.append(0)
    return result
    """
    
    logger.info("\nAnalyzing code:")
    logger.info(code_to_analyze)
    
    analysis = await code_agent.analyze_code(code_to_analyze, "python")
    
    logger.info("\nCode analysis results:")
    logger.info(f"Language: {analysis['language']}")
    logger.info(f"Complexity: Cyclomatic={analysis['complexity']['cyclomatic_complexity']}, Cognitive={analysis['complexity']['cognitive_complexity']}")
    
    if analysis["issues"]:
        logger.info("\nPotential issues:")
        for issue in analysis["issues"]:
            logger.info(f"- {issue['description']} (Severity: {issue['severity']})")
    else:
        logger.info("\nNo issues found.")
    
    if analysis["similar_code"]:
        logger.info("\nSimilar code snippets found:")
        for i, similar in enumerate(analysis["similar_code"]):
            logger.info(f"{i+1}. Similarity: {similar['similarity']:.4f}")
            logger.info(f"   Description: {similar['description']}")
    
    # Execute code
    code_to_execute = """
def calculate_sum(numbers):
    return sum(numbers)

result = calculate_sum([1, 2, 3, 4, 5])
print(f"The sum is: {result}")
    """
    
    logger.info("\nExecuting code:")
    logger.info(code_to_execute)
    
    execution_result = await code_agent.execute_code(
        code=code_to_execute,
        language="python"
    )
    
    logger.info("\nExecution results:")
    logger.info(f"Success: {execution_result['execution_successful']}")
    
    if execution_result["execution_successful"]:
        logger.info(f"Output: {execution_result['output']}")
        logger.info(f"Execution time: {execution_result['execution_time']:.4f} seconds")
    else:
        logger.info(f"Error: {execution_result['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 