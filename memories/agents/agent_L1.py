import faiss
import numpy as np
from gensim.models import KeyedVectors
import os
import pickle
from typing import Dict, List, Any, Optional
import pandas as pd
import duckdb
from memories.data_acquisition.data_connectors import get_word_embedding

# Module-level cache for word vectors
_WORD_VECTORS = None

class Agent_L1:
    def __init__(self, instance_id: str, search_term: str):
        """
        Initialize L1 Agent for similar column search.
        
        Args:
            instance_id (str): Instance ID for FAISS storage
            search_term (str): Term to search for similar columns
        """
        from memories.agents.agent_config import get_faiss_storage
        
        self.instance_id = instance_id
        self.search_term = search_term
        self.faiss_storage = get_faiss_storage(instance_id)
        
    def process(self) -> Dict[str, Any]:
        """
        Process the search term to find similar columns.
        
        Returns:
            Dict containing:
                - status: 'success' or 'error'
                - similar_columns: List of similar column metadata (if success)
                - error: Error message (if error)
        """
        try:
            if not self.faiss_storage:
                return {
                    "status": "error",
                    "error": "FAISS storage not initialized"
                }
            
            # Get embedding for search term
            search_embedding = get_word_embedding(self.search_term)
            
            # Search in FAISS index
            k = 5  # Number of similar columns to return
            D, I = self.faiss_storage['index'].search(
                np.array([search_embedding], dtype=np.float32), 
                k
            )
            
            # Check if any results were found
            if len(I[0]) == 0 or I[0][0] == -1:
                return {
                    "status": "success",
                    "similar_columns": [],
                    "message": f"No similar columns found for '{self.search_term}'"
                }
            
            # Get metadata for similar columns
            similar_columns = []
            for idx, distance in zip(I[0], D[0]):
                if idx != -1:  # Valid index
                    metadata = self.faiss_storage['metadata'][idx].copy()
                    metadata['distance'] = float(distance)
                    similar_columns.append(metadata)
            
            # If no valid columns found after filtering
            if not similar_columns:
                return {
                    "status": "success",
                    "similar_columns": [],
                    "message": f"No valid columns found for '{self.search_term}'"
                }
            
            return {
                "status": "success",
                "similar_columns": similar_columns,
                "message": f"Found {len(similar_columns)} similar columns"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_column_info(self, column_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific column.
        
        Args:
            column_name (str): Name of the column to get info for
            
        Returns:
            Dict containing column metadata or None if not found
        """
        try:
            for metadata in self.faiss_storage['metadata']:
                if metadata['column_name'] == column_name:
                    return metadata
            return None
        except Exception as e:
            print(f"Error getting column info: {str(e)}")
            return None

def main():
    """
    Example usage of Agent_L1 with file_path, geometry_column, and geometry_type provided.
    """
    # Example query and instance ID, with added file_path, geometry_column and geometry_type.
    instance_id = "126324854065696"  # Replace with your instance ID.
    query = "hospital"               # Replace with your query.
    file_path = os.path.join(os.getenv("PROJECT_ROOT", ""), "data", "parquet", "example.parquet")
    geometry_column = "geom"         # Replace with your geometry column name.
    geometry_type = "polygon"        # Replace with your geometry type if needed.
    
    # Create and run agent.
    agent = Agent_L1(instance_id, query)
    result = agent.process()
    
    # Print results.
    if result["status"] == "success":
        print(f"\nQuery: {result['search_term']}")
        print(f"Instance ID: {result['instance_id']}")
        print("\nSimilar columns:")
        for col in result["similar_columns"]:
            print(f"\n{col['rank']}. Column: {col['column_name']}")
            print(f"   File: {col['file_name']}")
            print(f"   Distance: {col['distance']:.4f}")
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
