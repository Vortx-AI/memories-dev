#!/usr/bin/env python3

import os
import logging
import pandas as pd
from pathlib import Path
from unittest.mock import patch
from memories.core.memory_manager import MemoryManager
from memories.core.memory_retrieval import MemoryRetrieval

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_search_geospatial():
    """Test the search_geospatial_data_in_bbox function."""
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config' / 'db_config.yml'
        
        # Create test config if it doesn't exist
        if not config_path.exists():
            os.makedirs(config_path.parent, exist_ok=True)
            test_config = {
                'database': {'path': './data/db', 'name': 'memories.db'},
                'memory': {
                    'base_path': './data/memory',
                    'hot': {'path': 'hot', 'max_size': 104857600},
                    'warm': {'path': 'warm', 'max_size': 1073741824},
                    'cold': {'path': 'cold', 'max_size': 10737418240},
                    'glacier': {'path': 'glacier', 'max_size': 107374182400}
                },
                'data': {
                    'storage': './data/storage',
                    'models': './data/models',
                    'cache': './data/cache'
                }
            }
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
        
        # Initialize memory manager with explicit config path
        memory_manager = MemoryManager()
        
        # Initialize memory retrieval
        memory_retrieval = MemoryRetrieval()
        memory_retrieval.cold = memory_manager.cold_memory
        
        # Define test parameters
        test_cases = [
            {
                "query_word": "water",
                "bbox": (-122.4194, 37.7749, -122.4089, 37.7858),  # San Francisco area
                "similarity_threshold": 0.7,
                "max_tokens": 15000
            },
            {
                "query_word": "building",
                "bbox": (-74.0060, 40.7128, -73.9950, 40.7218),  # New York area
                "similarity_threshold": 0.7,
                "max_tokens": 15000
            }
        ]
        
        # Mock get_similar_columns to return empty results
        with patch.object(MemoryRetrieval, 'get_similar_columns', return_value=[]):
            # Run tests
            for i, test_case in enumerate(test_cases, 1):
                logger.info(f"\nRunning test case {i}:")
                logger.info(f"Query word: {test_case['query_word']}")
                logger.info(f"Bounding box: {test_case['bbox']}")
                
                try:
                    results = memory_retrieval.search_geospatial_data_in_bbox(
                        query_word=test_case['query_word'],
                        bbox=test_case['bbox'],
                        similarity_threshold=test_case['similarity_threshold'],
                        max_tokens=test_case['max_tokens']
                    )
                    
                    # Test should pass with empty results since we mocked empty similar columns
                    assert isinstance(results, pd.DataFrame), "Result should be a pandas DataFrame"
                    assert results.empty, "Result should be empty when no similar columns found"
                    logger.info("Test passed: Result is an empty pandas DataFrame (expected)")
                        
                except Exception as e:
                    logger.error(f"Error in test case {i}: {str(e)}")
                    raise  # Re-raise the exception to fail the test
                    
    except Exception as e:
        logger.error(f"Error initializing test: {str(e)}")
        raise  # Re-raise the exception to fail the test

if __name__ == "__main__":
    test_search_geospatial() 