#!/usr/bin/env python3
"""
Multimodal AI Assistant
----------------------------------
This example demonstrates how to use the Memories-Dev framework to create
a multimodal AI assistant that can process and understand both text and image data,
storing and retrieving information across modalities.
"""

import os
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import base64
import json
from PIL import Image
import io
from dotenv import load_dotenv

from memories import MemoryStore, Config
from memories.models import BaseModel
from memories.utils.text import TextProcessor
from memories.utils.earth import VectorProcessor
from memories.utils.query_understanding import QueryUnderstanding
from memories.utils.response_generation import ResponseGeneration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MultimodalAIAssistant(BaseModel):
    """AI assistant that can process and understand both text and image data."""
    
    def __init__(
        self, 
        memory_store: MemoryStore, 
        text_embedding_model: str = "all-MiniLM-L6-v2",
        image_embedding_model: str = "clip-ViT-B-32",
        embedding_dimension: int = 512,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize the Multimodal AI Assistant.
        
        Args:
            memory_store: Memory store for maintaining embeddings
            text_embedding_model: Name of the text embedding model to use
            image_embedding_model: Name of the image embedding model to use
            embedding_dimension: Dimension of the embedding vectors
            similarity_threshold: Threshold for similarity matching
        """
        super().__init__(name="multimodal_ai_assistant")
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
        self.vector_processor = VectorProcessor()
        self.query_understanding = QueryUnderstanding()
        self.response_generator = ResponseGeneration()
        
        self.text_embedding_model = text_embedding_model
        self.image_embedding_model = image_embedding_model
        self.embedding_dimension = embedding_dimension
        self.similarity_threshold = similarity_threshold
        
        # Initialize memory caches
        self.text_embedding_cache = {}
        self.image_embedding_cache = {}
        self.multimodal_memory_cache = {}
        
        logger.info(f"Multimodal AI Assistant initialized")
        logger.info(f"Text embedding model: {text_embedding_model}")
        logger.info(f"Image embedding model: {image_embedding_model}")
    
    async def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process and embed text data.
        
        Args:
            text: Text to process
            metadata: Additional metadata about the text
            
        Returns:
            Dictionary containing the processed text data
        """
        # Preprocess text
        processed_text = self.text_processor.preprocess(text)
        
        # Extract entities and keywords
        entities = self.text_processor.extract_entities(processed_text)
        keywords = self.text_processor.extract_keywords(processed_text)
        
        # Generate embedding
        embedding = self._generate_text_embedding(processed_text)
        
        # Create text record
        text_record = {
            "type": "text",
            "text": text,
            "processed_text": processed_text,
            "embedding": embedding,
            "entities": [e._asdict() for e in entities],
            "keywords": keywords,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in memory
        memory_id = self._store_in_memory(text_record)
        text_record["memory_id"] = memory_id
        
        # Update cache
        text_hash = hash(text) % 10000
        self.text_embedding_cache[text_hash] = text_record
        
        return text_record
    
    async def process_image(self, image_path: str, caption: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process and embed image data.
        
        Args:
            image_path: Path to the image file
            caption: Optional caption for the image
            metadata: Additional metadata about the image
            
        Returns:
            Dictionary containing the processed image data
        """
        # Load and preprocess image
        try:
            image = Image.open(image_path)
            # Resize image for consistent processing
            image = image.resize((224, 224))
            
            # Convert to base64 for storage
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Generate image embedding
            embedding = self._generate_image_embedding(image)
            
            # Process caption if provided
            caption_embedding = None
            caption_entities = []
            caption_keywords = []
            
            if caption:
                processed_caption = self.text_processor.preprocess(caption)
                caption_embedding = self._generate_text_embedding(processed_caption)
                caption_entities = self.text_processor.extract_entities(processed_caption)
                caption_keywords = self.text_processor.extract_keywords(processed_caption)
            
            # Create image record
            image_record = {
                "type": "image",
                "image_path": image_path,
                "image_data": img_str,
                "caption": caption,
                "embedding": embedding,
                "caption_embedding": caption_embedding,
                "caption_entities": [e._asdict() for e in caption_entities] if caption else [],
                "caption_keywords": caption_keywords if caption else [],
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in memory
            memory_id = self._store_in_memory(image_record)
            image_record["memory_id"] = memory_id
            
            # Update cache
            image_hash = hash(image_path) % 10000
            self.image_embedding_cache[image_hash] = image_record
            
            return image_record
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {"error": str(e)}
    
    async def create_multimodal_memory(self, text_data: str, image_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a multimodal memory combining text and image data.
        
        Args:
            text_data: Text component of the memory
            image_path: Path to the image component
            metadata: Additional metadata
            
        Returns:
            Dictionary containing the multimodal memory
        """
        # Process text and image separately
        text_record = await self.process_text(text_data, metadata)
        image_record = await self.process_image(image_path, caption=text_data, metadata=metadata)
        
        if "error" in image_record:
            return {"error": image_record["error"]}
        
        # Create combined embedding (average of text and image embeddings)
        combined_embedding = self._combine_embeddings(
            text_record["embedding"], 
            image_record["embedding"]
        )
        
        # Create multimodal record
        multimodal_record = {
            "type": "multimodal",
            "text_component": text_record,
            "image_component": image_record,
            "combined_embedding": combined_embedding,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in memory
        memory_id = self._store_in_memory(multimodal_record, memory_type="hot")
        multimodal_record["memory_id"] = memory_id
        
        # Update cache
        mm_hash = hash(f"{text_data}_{image_path}") % 10000
        self.multimodal_memory_cache[mm_hash] = multimodal_record
        
        return multimodal_record
    
    async def search_memories(self, query: str, modality: str = "all", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for memories similar to the query.
        
        Args:
            query: Query text to search for
            modality: Type of memories to search ("text", "image", "multimodal", or "all")
            top_k: Number of top results to return
            
        Returns:
            List of similar memories with similarity scores
        """
        # Process query to understand intent
        query_intent = self.query_understanding.analyze_query(query)
        
        # Generate query embedding
        query_embedding = self._generate_text_embedding(self.text_processor.preprocess(query))
        
        # Retrieve memories based on modality
        if modality == "text":
            memories = list(self.text_embedding_cache.values())
        elif modality == "image":
            memories = list(self.image_embedding_cache.values())
        elif modality == "multimodal":
            memories = list(self.multimodal_memory_cache.values())
        else:  # "all"
            memories = (
                list(self.text_embedding_cache.values()) + 
                list(self.image_embedding_cache.values()) + 
                list(self.multimodal_memory_cache.values())
            )
        
        # Calculate similarities
        similarities = []
        for memory in memories:
            # Determine which embedding to compare with
            if memory["type"] == "text":
                memory_embedding = memory["embedding"]
            elif memory["type"] == "image":
                # For images, compare with caption embedding if available, otherwise image embedding
                memory_embedding = memory.get("caption_embedding") or memory["embedding"]
            else:  # "multimodal"
                memory_embedding = memory["combined_embedding"]
            
            similarity = self._calculate_similarity(query_embedding, memory_embedding)
            
            if similarity >= self.similarity_threshold:
                similarities.append({
                    "memory": memory,
                    "similarity": similarity,
                    "type": memory["type"]
                })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Return top k results
        return similarities[:top_k]
    
    async def generate_response(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response based on the query and retrieved context.
        
        Args:
            query: User query
            context: Retrieved context information
            
        Returns:
            Generated response with metadata
        """
        # Analyze query intent
        query_intent = self.query_understanding.analyze_query(query)
        
        # Extract relevant information from context
        relevant_info = []
        for item in context:
            memory = item["memory"]
            memory_type = memory["type"]
            
            if memory_type == "text":
                relevant_info.append({
                    "type": "text",
                    "content": memory["text"],
                    "relevance": item["similarity"],
                    "entities": memory.get("entities", []),
                    "keywords": memory.get("keywords", [])
                })
            elif memory_type == "image":
                relevant_info.append({
                    "type": "image",
                    "content": memory.get("caption", "Image without caption"),
                    "image_path": memory["image_path"],
                    "relevance": item["similarity"],
                    "entities": memory.get("caption_entities", []),
                    "keywords": memory.get("caption_keywords", [])
                })
            else:  # "multimodal"
                relevant_info.append({
                    "type": "multimodal",
                    "text_content": memory["text_component"]["text"],
                    "image_path": memory["image_component"]["image_path"],
                    "relevance": item["similarity"],
                    "entities": memory["text_component"].get("entities", []),
                    "keywords": memory["text_component"].get("keywords", [])
                })
        
        # Generate response
        response = self.response_generator.generate(
            query=query,
            context=relevant_info,
            intent=query_intent
        )
        
        # Store the interaction in memory
        interaction_record = {
            "type": "interaction",
            "query": query,
            "response": response,
            "context": relevant_info,
            "intent": query_intent,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory_store.warm_memory.store(interaction_record)
        
        return {
            "response": response,
            "intent": query_intent,
            "context_used": len(relevant_info),
            "modalities_used": list(set(item["type"] for item in relevant_info))
        }
    
    def _generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text (simulated)."""
        # In a real implementation, this would use a text embedding model
        # For demonstration, we'll generate a random vector
        
        # Use hash of text to ensure same text gets same embedding
        text_hash = hash(text)
        np.random.seed(text_hash)
        
        # Generate random embedding vector
        embedding = np.random.normal(0, 1, self.embedding_dimension)
        
        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def _generate_image_embedding(self, image: Image.Image) -> List[float]:
        """Generate embedding vector for image (simulated)."""
        # In a real implementation, this would use an image embedding model like CLIP
        # For demonstration, we'll generate a random vector
        
        # Use hash of image data to ensure same image gets same embedding
        image_hash = hash(image.tobytes())
        np.random.seed(image_hash)
        
        # Generate random embedding vector
        embedding = np.random.normal(0, 1, self.embedding_dimension)
        
        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def _combine_embeddings(self, embedding1: List[float], embedding2: List[float]) -> List[float]:
        """Combine two embeddings into a single multimodal embedding."""
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Simple averaging of embeddings
        combined = (vec1 + vec2) / 2
        
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
        memory_id = f"{record['type']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(record)) % 1000}"
        
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

def simulate_image_data() -> List[Dict[str, Any]]:
    """Generate simulated image data for demonstration."""
    # In a real implementation, these would be paths to actual images
    return [
        {
            "path": "examples/data/simulated_image1.jpg",
            "caption": "A neural network architecture diagram showing multiple layers of neurons.",
            "metadata": {
                "topic": "AI Architecture",
                "importance": 0.85
            }
        },
        {
            "path": "examples/data/simulated_image2.jpg",
            "caption": "A visualization of a transformer model's attention mechanism.",
            "metadata": {
                "topic": "Transformer Models",
                "importance": 0.9
            }
        },
        {
            "path": "examples/data/simulated_image3.jpg",
            "caption": "A comparison chart of different machine learning algorithms and their performance.",
            "metadata": {
                "topic": "ML Algorithms",
                "importance": 0.8
            }
        },
        {
            "path": "examples/data/simulated_image4.jpg",
            "caption": "A robot using computer vision to identify and pick up objects.",
            "metadata": {
                "topic": "Computer Vision",
                "importance": 0.75
            }
        },
        {
            "path": "examples/data/simulated_image5.jpg",
            "caption": "A dashboard showing real-time natural language processing of customer feedback.",
            "metadata": {
                "topic": "NLP Applications",
                "importance": 0.8
            }
        }
    ]

def simulate_text_data() -> List[Dict[str, str]]:
    """Generate simulated text data for demonstration."""
    return [
        {
            "content": "Transformer models have revolutionized natural language processing by using self-attention mechanisms to process sequential data more effectively than previous approaches.",
            "metadata": {
                "topic": "Transformer Models",
                "importance": 0.9
            }
        },
        {
            "content": "Computer vision systems can now recognize objects, faces, and actions in images and videos with accuracy approaching or exceeding human capabilities in many tasks.",
            "metadata": {
                "topic": "Computer Vision",
                "importance": 0.85
            }
        },
        {
            "content": "Reinforcement learning enables AI agents to learn optimal behavior through trial and error interactions with an environment, guided by reward signals.",
            "metadata": {
                "topic": "Reinforcement Learning",
                "importance": 0.8
            }
        },
        {
            "content": "Large language models like GPT-4 can generate coherent text, translate languages, write creative content, and answer questions based on their training on vast text corpora.",
            "metadata": {
                "topic": "Large Language Models",
                "importance": 0.95
            }
        },
        {
            "content": "Multimodal AI systems that can process both text and images are enabling new applications like visual question answering and image captioning.",
            "metadata": {
                "topic": "Multimodal AI",
                "importance": 0.9
            }
        }
    ]

def create_simulated_image(path: str, caption: str):
    """Create a simulated image file for demonstration purposes."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Create a simple colored image with text
    img = Image.new('RGB', (224, 224), color=(73, 109, 137))
    
    # Save the image
    img.save(path)
    
    logger.info(f"Created simulated image at {path}")

async def main():
    """Main execution function."""
    # Initialize memory system
    config = Config(
        storage_path="./multimodal_assistant_data",
        hot_memory_size=50,
        warm_memory_size=500,
        cold_memory_size=5000
    )
    
    memory_store = MemoryStore(config)
    
    # Initialize multimodal AI assistant
    assistant = MultimodalAIAssistant(memory_store)
    
    # Create data directories
    os.makedirs("examples/data", exist_ok=True)
    
    # Generate simulated data
    text_data = simulate_text_data()
    image_data = simulate_image_data()
    
    # Create simulated images
    for image in image_data:
        create_simulated_image(image["path"], image["caption"])
    
    # Process text data
    logger.info("Processing text data...")
    for item in text_data:
        await assistant.process_text(item["content"], item["metadata"])
    
    # Process image data
    logger.info("\nProcessing image data...")
    for item in image_data:
        await assistant.process_image(item["path"], item["caption"], item["metadata"])
    
    # Create multimodal memories
    logger.info("\nCreating multimodal memories...")
    for i in range(min(len(text_data), len(image_data))):
        text_item = text_data[i]
        image_item = image_data[i]
        
        # Combine related text and image
        await assistant.create_multimodal_memory(
            text_item["content"],
            image_item["path"],
            {**text_item["metadata"], **image_item["metadata"]}
        )
    
    # Perform multimodal search
    query = "How do transformer models work?"
    logger.info(f"\nSearching for information related to: '{query}'")
    
    search_results = await assistant.search_memories(query, modality="all", top_k=3)
    
    logger.info("\nTop relevant information:")
    for i, result in enumerate(search_results):
        memory = result["memory"]
        logger.info(f"{i+1}. Relevance: {result['similarity']:.4f}, Type: {memory['type']}")
        
        if memory["type"] == "text":
            logger.info(f"   Content: {memory['text']}")
        elif memory["type"] == "image":
            logger.info(f"   Image: {memory['image_path']}")
            logger.info(f"   Caption: {memory.get('caption', 'No caption')}")
        else:  # multimodal
            logger.info(f"   Text: {memory['text_component']['text']}")
            logger.info(f"   Image: {memory['image_component']['image_path']}")
    
    # Generate response to user query
    logger.info("\nGenerating response to user query...")
    response_data = await assistant.generate_response(query, search_results)
    
    logger.info(f"\nResponse: {response_data['response']}")
    logger.info(f"Intent detected: {response_data['intent']}")
    logger.info(f"Context used: {response_data['context_used']} items")
    logger.info(f"Modalities used: {', '.join(response_data['modalities_used'])}")
    
    # Try another query that should retrieve image information
    image_query = "Show me visualizations of neural networks"
    logger.info(f"\nSearching for visual information: '{image_query}'")
    
    image_results = await assistant.search_memories(image_query, modality="image", top_k=2)
    
    logger.info("\nTop relevant images:")
    for i, result in enumerate(image_results):
        memory = result["memory"]
        logger.info(f"{i+1}. Relevance: {result['similarity']:.4f}")
        logger.info(f"   Image: {memory['image_path']}")
        logger.info(f"   Caption: {memory.get('caption', 'No caption')}")
    
    # Generate response to image query
    logger.info("\nGenerating response to image query...")
    image_response = await assistant.generate_response(image_query, image_results)
    
    logger.info(f"\nResponse: {image_response['response']}")
    logger.info(f"Modalities used: {', '.join(image_response['modalities_used'])}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 