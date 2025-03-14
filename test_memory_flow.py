#!/usr/bin/env python
"""Test script to demonstrate the complete memory flow: add -> index -> query."""

import asyncio
import logging
from memories.core.memory_manager import MemoryManager
from memories.core.memory_index import MemoryIndex
from memories.core.memory_query import MemoryQuery
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the complete memory flow test."""
    try:
        # Initialize components
        memory_manager = MemoryManager()
        memory_index = MemoryIndex()
        memory_query = MemoryQuery(similarity_threshold=0.7)
        
        # Step 1: Add test data to red_hot tier
        # Create some test vectors (simulating embeddings)
        test_vectors = np.random.rand(5, 384).astype(np.float32)  # 5 vectors of dimension 384
        test_metadata = [
            {
                "id": f"doc_{i}",
                "content": f"This is test document {i}",
                "type": "text",
                "tags": ["test", f"tag_{i}"]
            }
            for i in range(5)
        ]
        
        logger.info("Adding test data to red_hot tier...")
        memory_manager._init_red_hot()
        for i, (vector, metadata) in enumerate(zip(test_vectors, test_metadata)):
            await memory_manager._red_hot_memory.add(
                vector=vector,
                metadata=metadata,
                data_id=metadata["id"]
            )
        logger.info("Test data added successfully")
        
        # Step 2: Index the data
        logger.info("Indexing data...")
        await memory_index.update_index("red_hot")
        logger.info("Data indexed successfully")
        
        # Step 3: Query the data
        logger.info("Performing test query...")
        # Create a test query vector (similar to one of our test vectors)
        query = "test document"
        results = await memory_query.search(
            query=query,
            tiers=["red_hot"],
            k=3,
            stop_on_first_match=True
        )
        
        # Get enhanced metadata
        enhanced_results = await memory_query.get_enhanced_metadata(results)
        
        # Print results
        logger.info("Query results:")
        for tier, tier_results in enhanced_results.items():
            logger.info(f"\nResults from {tier} tier:")
            for result in tier_results:
                logger.info(f"- Document ID: {result.get('data_id')}")
                logger.info(f"  Distance: {result.get('distance'):.4f}")
                logger.info(f"  Metadata: {result.get('metadata', {})}")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 