#!/usr/bin/env python3
"""
AI Semantic Search and Knowledge Retrieval Agent
----------------------------------
This example demonstrates how to use the Memories-Dev framework to create
an AI agent that generates, stores, and searches text embeddings for
semantic similarity and knowledge retrieval.
"""

import os
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dotenv import load_dotenv

from memories.core.memory_store import MemoryStore
from memories.config import Config
from memories.models import BaseModel
from memories.utils.text import TextProcessor
from memories.utils.earth import VectorProcessor

# Define simple versions of these classes for the example
class QueryUnderstanding:
    def analyze_query(self, query):
        return {"intent": "search", "entities": [], "keywords": []}

class ResponseGeneration:
    def generate(self, query, context, intent):
        return f"Response to query: {query} based on {len(context)} context items"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AISemanticAgent(BaseModel):
    """AI agent specialized in semantic search and knowledge retrieval."""
    
    def __init__(
        self, 
        memory_store: MemoryStore, 
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
        similarity_threshold: float = 0.75
    ):
        """
        Initialize the AI Semantic Agent.
        
        Args:
            memory_store: Memory store for maintaining embeddings
            embedding_model: Name of the embedding model to use
            embedding_dimension: Dimension of the embedding vectors
            similarity_threshold: Threshold for similarity matching
        """
        super().__init__()
        self.memory_store = memory_store
        self.text_processor = TextProcessor()
        self.vector_processor = VectorProcessor()
        self.query_understanding = QueryUnderstanding()
        self.response_generator = ResponseGeneration()
        
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.similarity_threshold = similarity_threshold
        
        # Initialize embedding cache
        self.embedding_cache = {}
        
        logger.info(f"AI Semantic Agent initialized with {embedding_model}")
        logger.info(f"Embedding dimension: {embedding_dimension}")
    
    async def embed_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate embeddings for a text and store them in memory.
        
        Args:
            text: Text to embed
            metadata: Additional metadata about the text
            
        Returns:
            Dictionary containing the embedding and metadata
        """
        # Preprocess text
        processed_text = self.text_processor.preprocess(text)
        
        # Extract entities and keywords
        entities = self.text_processor.extract_entities(processed_text)
        keywords = self.text_processor.extract_keywords(processed_text)
        
        # Generate embedding
        embedding = self._generate_embedding(processed_text)
        
        # Create embedding record
        embedding_record = {
            "text": text,
            "processed_text": processed_text,
            "embedding": embedding,
            "entities": [e._asdict() for e in entities],
            "keywords": keywords,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in memory
        self._store_embedding(embedding_record)
        
        # Update cache
        text_hash = hash(text) % 10000
        self.embedding_cache[text_hash] = embedding_record
        
        return embedding_record
    
    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for texts with similar embeddings to the query.
        
        Args:
            query: Query text to search for
            top_k: Number of top results to return
            
        Returns:
            List of similar texts with similarity scores
        """
        # Process query to understand intent
        query_intent = self.query_understanding.analyze_query(query)
        
        # Generate query embedding
        query_embedding = self._generate_embedding(self.text_processor.preprocess(query))
        
        # Retrieve all embeddings from memory
        all_embeddings = self._retrieve_all_embeddings()
        
        # Calculate similarities
        similarities = []
        for record in all_embeddings:
            similarity = self._calculate_similarity(query_embedding, record["embedding"])
            if similarity >= self.similarity_threshold:
                similarities.append({
                    "text": record["text"],
                    "similarity": similarity,
                    "timestamp": record["timestamp"],
                    "metadata": record["metadata"],
                    "entities": record.get("entities", []),
                    "keywords": record.get("keywords", [])
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
            relevant_info.append({
                "text": item["text"],
                "relevance": item["similarity"],
                "entities": item.get("entities", []),
                "keywords": item.get("keywords", [])
            })
        
        # Generate response
        response = self.response_generator.generate(
            query=query,
            context=relevant_info,
            intent=query_intent
        )
        
        # Store the interaction in memory (just log it for demonstration)
        interaction_record = {
            "query": query,
            "response": response,
            "context": relevant_info,
            "intent": query_intent,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log the interaction
        print(f"Stored interaction for query: {query}")
        logger.info(f"Stored interaction for query: {query}")
        
        return {
            "response": response,
            "intent": query_intent,
            "context_used": len(relevant_info)
        }
    
    async def cluster_embeddings(self, num_clusters: int = 3) -> Dict[str, Any]:
        """
        Cluster stored embeddings to find patterns.
        
        Args:
            num_clusters: Number of clusters to create
            
        Returns:
            Dictionary containing cluster information
        """
        # Retrieve all embeddings
        all_embeddings = self._retrieve_all_embeddings()
        
        if len(all_embeddings) < num_clusters:
            return {"error": "Not enough embeddings for clustering"}
        
        # Extract embedding vectors
        embedding_vectors = [record["embedding"] for record in all_embeddings]
        
        # Perform clustering (simulated for demonstration)
        clusters = self._simulate_clustering(embedding_vectors, num_clusters)
        
        # Assign clusters to records
        clustered_data = []
        for i, record in enumerate(all_embeddings):
            clustered_data.append({
                "text": record["text"],
                "cluster": clusters[i],
                "timestamp": record["timestamp"],
                "metadata": record["metadata"]
            })
        
        # Group by cluster
        cluster_groups = {}
        for item in clustered_data:
            cluster = item["cluster"]
            if cluster not in cluster_groups:
                cluster_groups[cluster] = []
            cluster_groups[cluster].append(item)
        
        # Analyze clusters to find common themes
        cluster_themes = {}
        for cluster_id, items in cluster_groups.items():
            # Extract all keywords from cluster items
            all_keywords = []
            for item in items:
                item_keywords = self.embedding_cache.get(hash(item["text"]) % 10000, {}).get("keywords", [])
                all_keywords.extend([kw for kw, _ in item_keywords])
            
            # Count keyword frequencies
            keyword_counts = {}
            for kw in all_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
            
            # Get top keywords as theme
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            cluster_themes[cluster_id] = [kw for kw, _ in top_keywords]
        
        return {
            "num_clusters": num_clusters,
            "total_embeddings": len(all_embeddings),
            "clusters": cluster_groups,
            "themes": cluster_themes
        }
    
    async def analyze_text_similarity(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Analyze the similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Dictionary containing similarity analysis
        """
        # Process texts
        processed_text1 = self.text_processor.preprocess(text1)
        processed_text2 = self.text_processor.preprocess(text2)
        
        # Extract entities and keywords
        entities1 = self.text_processor.extract_entities(processed_text1)
        entities2 = self.text_processor.extract_entities(processed_text2)
        
        keywords1 = self.text_processor.extract_keywords(processed_text1)
        keywords2 = self.text_processor.extract_keywords(processed_text2)
        
        # Generate embeddings
        embedding1 = self._generate_embedding(processed_text1)
        embedding2 = self._generate_embedding(processed_text2)
        
        # Calculate similarity
        similarity = self._calculate_similarity(embedding1, embedding2)
        
        # Analyze common terms
        common_terms = self._analyze_common_terms(processed_text1, processed_text2)
        
        # Find common entities
        common_entities = []
        entity_texts1 = [e.text.lower() for e in entities1]
        for entity in entities2:
            if entity.text.lower() in entity_texts1:
                common_entities.append(entity.text)
        
        # Find common keywords
        common_keywords = []
        kw_texts1 = [kw for kw, _ in keywords1]
        for kw, _ in keywords2:
            if kw in kw_texts1:
                common_keywords.append(kw)
        
        return {
            "similarity_score": similarity,
            "common_terms": common_terms,
            "common_entities": common_entities,
            "common_keywords": common_keywords,
            "interpretation": self._interpret_similarity(similarity),
            "texts": {
                "text1": {
                    "original": text1,
                    "entities": [e._asdict() for e in entities1],
                    "keywords": keywords1
                },
                "text2": {
                    "original": text2,
                    "entities": [e._asdict() for e in entities2],
                    "keywords": keywords2
                }
            }
        }
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text (simulated)."""
        # In a real implementation, this would use an embedding model
        # For demonstration, we'll generate a random vector
        
        # Use hash of text to ensure same text gets same embedding
        text_hash = abs(hash(text)) % (2**32 - 1)  # Ensure seed is within valid range
        np.random.seed(text_hash)
        
        # Generate random embedding vector
        embedding = np.random.normal(0, 1, self.embedding_dimension)
        
        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
    
    def _store_embedding(self, embedding_record: Dict[str, Any]) -> None:
        """Store embedding in memory."""
        # For demonstration purposes, we'll just store in the cache
        # In a real implementation, this would store in the memory store
        text_hash = hash(embedding_record["text"]) % 10000
        self.embedding_cache[text_hash] = embedding_record
        
        # Log the storage
        print(f"Stored embedding for text: {embedding_record['text'][:30]}...")
        logger.info(f"Stored embedding for text: {embedding_record['text'][:30]}...")
    
    def _retrieve_all_embeddings(self) -> List[Dict[str, Any]]:
        """Retrieve all embeddings from memory."""
        # In a real implementation, this would query the memory store
        # For demonstration, we'll use the cache
        
        return list(self.embedding_cache.values())
    
    def _simulate_clustering(self, embedding_vectors: List[List[float]], num_clusters: int) -> List[int]:
        """Simulate clustering of embeddings (for demonstration)."""
        # In a real implementation, this would use K-means or another clustering algorithm
        # For demonstration, we'll assign random clusters
        
        return np.random.randint(0, num_clusters, len(embedding_vectors)).tolist()
    
    def _analyze_common_terms(self, text1: str, text2: str) -> List[str]:
        """Analyze common terms between two texts."""
        # Split texts into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Find common words
        common = words1.intersection(words2)
        
        # Return up to 5 common words
        return list(common)[:5]
    
    def _interpret_similarity(self, similarity: float) -> str:
        """Interpret similarity score."""
        if similarity > 0.9:
            return "Very high similarity - texts are nearly identical in meaning"
        elif similarity > 0.8:
            return "High similarity - texts convey very similar concepts"
        elif similarity > 0.7:
            return "Moderate similarity - texts share significant meaning"
        elif similarity > 0.5:
            return "Some similarity - texts have some common concepts"
        else:
            return "Low similarity - texts are mostly unrelated"

def simulate_knowledge_base() -> List[Dict[str, str]]:
    """Generate simulated knowledge base for demonstration."""
    return [
        {
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data. It enables computers to improve their performance on a task without being explicitly programmed.",
            "category": "AI Fundamentals",
            "importance": 0.9
        },
        {
            "title": "Neural Networks Explained",
            "content": "Neural networks are computing systems inspired by the biological neural networks in animal brains. They consist of artificial neurons that can learn to perform tasks by considering examples, without being programmed with task-specific rules.",
            "category": "Deep Learning",
            "importance": 0.85
        },
        {
            "title": "Natural Language Processing",
            "content": "Natural Language Processing (NLP) is a field of AI that gives machines the ability to read, understand, and derive meaning from human languages. It combines computational linguistics with statistical and machine learning models.",
            "category": "AI Applications",
            "importance": 0.8
        },
        {
            "title": "Computer Vision Systems",
            "content": "Computer vision is an interdisciplinary field that deals with how computers can gain high-level understanding from digital images or videos. It seeks to automate tasks that the human visual system can do.",
            "category": "AI Applications",
            "importance": 0.75
        },
        {
            "title": "Reinforcement Learning",
            "content": "Reinforcement learning is an area of machine learning concerned with how software agents ought to take actions in an environment to maximize some notion of cumulative reward. It differs from supervised learning in that correct input/output pairs need not be presented.",
            "category": "AI Techniques",
            "importance": 0.8
        },
        {
            "title": "Transformer Models",
            "content": "Transformer models are a type of neural network architecture that has revolutionized NLP tasks. They use self-attention mechanisms to process sequential data, allowing them to capture long-range dependencies more effectively than previous approaches.",
            "category": "Deep Learning",
            "importance": 0.9
        },
        {
            "title": "AI Ethics Considerations",
            "content": "AI ethics involves the moral issues and risks that arise from the development and deployment of artificial intelligence. Key concerns include privacy, bias, transparency, accountability, and the potential impact on employment and society.",
            "category": "AI Ethics",
            "importance": 0.95
        },
        {
            "title": "Large Language Models",
            "content": "Large Language Models (LLMs) are AI systems trained on vast amounts of text data that can generate human-like text, translate languages, write different kinds of creative content, and answer questions in an informative way.",
            "category": "AI Applications",
            "importance": 0.9
        },
        {
            "title": "Multimodal AI Systems",
            "content": "Multimodal AI systems can process and relate information from multiple data sources such as text, images, audio, and video. They enable more comprehensive understanding by integrating different types of data.",
            "category": "Advanced AI",
            "importance": 0.85
        },
        {
            "title": "AI for Scientific Discovery",
            "content": "AI is accelerating scientific discovery across fields like drug development, materials science, and climate modeling. Machine learning models can identify patterns in complex data and suggest new hypotheses for researchers to explore.",
            "category": "AI Applications",
            "importance": 0.8
        }
    ]

async def main():
    """Main execution function."""
    # Initialize memory system
    print("Initializing memory system...")
    config = Config(
        storage_path="./ai_semantic_agent_data",
        hot_memory_size=50,
        warm_memory_size=500,
        cold_memory_size=5000
    )
    
    # Initialize memory store without passing config
    print("Initializing memory store...")
    memory_store = MemoryStore()
    
    # Initialize AI semantic agent
    print("Initializing AI semantic agent...")
    semantic_agent = AISemanticAgent(memory_store)
    
    # Generate knowledge base
    print("Generating knowledge base...")
    knowledge_base = simulate_knowledge_base()
    
    # Embed knowledge base articles
    print("Embedding knowledge base articles...")
    logger.info("Embedding knowledge base articles...")
    for article in knowledge_base:
        print(f"Embedding article: {article['title']}")
        metadata = {
            "title": article["title"],
            "category": article["category"],
            "importance": article["importance"]
        }
        await semantic_agent.embed_text(article["content"], metadata)
    
    # Perform semantic search
    query = "How do neural networks relate to the human brain?"
    print(f"\nSearching for information related to: '{query}'")
    logger.info(f"\nSearching for information related to: '{query}'")
    
    similar_texts = await semantic_agent.search_similar(query, top_k=3)
    
    print("\nTop relevant information:")
    logger.info("\nTop relevant information:")
    for i, result in enumerate(similar_texts):
        print(f"{i+1}. Relevance: {result['similarity']:.4f}")
        print(f"   Title: {result['metadata']['title']}")
        print(f"   Content: {result['text']}")
        logger.info(f"{i+1}. Relevance: {result['similarity']:.4f}")
        logger.info(f"   Title: {result['metadata']['title']}")
        logger.info(f"   Content: {result['text']}")
    
    # Generate response to user query
    print("\nGenerating response to user query...")
    logger.info("\nGenerating response to user query...")
    response_data = await semantic_agent.generate_response(query, similar_texts)
    
    print(f"\nResponse: {response_data['response']}")
    print(f"Intent detected: {response_data['intent']}")
    print(f"Context used: {response_data['context_used']} articles")
    logger.info(f"\nResponse: {response_data['response']}")
    logger.info(f"Intent detected: {response_data['intent']}")
    logger.info(f"Context used: {response_data['context_used']} articles")
    
    # Perform clustering analysis
    print("\nClustering knowledge base articles...")
    logger.info("\nClustering knowledge base articles...")
    clusters = await semantic_agent.cluster_embeddings(num_clusters=3)
    
    print(f"\nFound {clusters['num_clusters']} knowledge clusters in {clusters['total_embeddings']} articles")
    logger.info(f"\nFound {clusters['num_clusters']} knowledge clusters in {clusters['total_embeddings']} articles")
    for cluster_id, items in clusters['clusters'].items():
        print(f"\nCluster {cluster_id} ({len(items)} articles):")
        print(f"Theme: {', '.join(clusters['themes'][cluster_id])}")
        logger.info(f"\nCluster {cluster_id} ({len(items)} articles):")
        logger.info(f"Theme: {', '.join(clusters['themes'][cluster_id])}")
        for item in items:
            print(f"- {item['metadata']['title']}")
            logger.info(f"- {item['metadata']['title']}")
    
    # Analyze similarity between two articles
    article1 = knowledge_base[1]["content"]  # Neural Networks
    article2 = knowledge_base[5]["content"]  # Transformer Models
    
    print("\nAnalyzing similarity between:")
    print(f"Article 1: '{knowledge_base[1]['title']}'")
    print(f"Article 2: '{knowledge_base[5]['title']}'")
    logger.info("\nAnalyzing similarity between:")
    logger.info(f"Article 1: '{knowledge_base[1]['title']}'")
    logger.info(f"Article 2: '{knowledge_base[5]['title']}'")
    
    similarity_analysis = await semantic_agent.analyze_text_similarity(article1, article2)
    
    print(f"\nSimilarity score: {similarity_analysis['similarity_score']:.4f}")
    print(f"Interpretation: {similarity_analysis['interpretation']}")
    logger.info(f"\nSimilarity score: {similarity_analysis['similarity_score']:.4f}")
    logger.info(f"Interpretation: {similarity_analysis['interpretation']}")
    
    if similarity_analysis['common_entities']:
        print(f"Common entities: {', '.join(similarity_analysis['common_entities'])}")
        logger.info(f"Common entities: {', '.join(similarity_analysis['common_entities'])}")
    
    if similarity_analysis['common_keywords']:
        print(f"Common keywords: {', '.join(similarity_analysis['common_keywords'])}")
        logger.info(f"Common keywords: {', '.join(similarity_analysis['common_keywords'])}")
        
    print("\nExample completed successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 