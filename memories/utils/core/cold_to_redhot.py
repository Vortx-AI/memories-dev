import logging
from pathlib import Path
import pandas as pd
import duckdb
import os
from typing import Dict, List, Tuple, Optional
from memories.core.red_hot import RedHotMemory
from memories.core.cold import ColdMemory
from memories.core.memory_manager import MemoryManager
import pyarrow.parquet as pq
import glob
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import sys

logger = logging.getLogger(__name__)

class ColdToRedHot:
    def __init__(self):
        """Initialize cold to red-hot transfer."""
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Set up data directories
        self.data_dir = os.path.join(project_root, "data")
        self.faiss_dir = os.path.join(self.data_dir, "red_hot")
        
        # Get memory manager instance and its connection
        self.memory_manager = MemoryManager()
        
        # Initialize components using existing connection
        self.cold = ColdMemory(self.memory_manager.con)
        self.red_hot = RedHotMemory()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Debug prints
        print("\nDebug info:")
        print(f"Project root: {project_root}")
        print(f"Data directory: {self.data_dir}")
        print(f"FAISS storage location: {self.faiss_dir}")
        print(f"RedHotMemory methods: {dir(self.red_hot)}")
        print(f"Has add_vector: {'add_vector' in dir(self.red_hot)}\n")
        
        logger.info(f"Initialized ColdToRedHot")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"FAISS storage location: {self.faiss_dir}")

    def get_schema_info(self, file_path: str):
        """Get schema information from a parquet file."""
        try:
            # Read parquet file schema using pandas directly
            df = pd.read_parquet(file_path)
            
            # Find geometry column by checking data types
            geometry_column = None
            for col, dtype in df.dtypes.items():
                if 'geometry' in str(dtype).lower():
                    geometry_column = col
                    logger.info(f"Found geometry column in {file_path}: {col} with type {dtype}")
                    break
            
            # Get schema information
            schema_info = {
                'file_path': file_path,
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'type': 'schema',
                'geometry_column': geometry_column  # Add the geometry column to schema info
            }
            
            # Create text representation for embedding
            column_text = " ".join(schema_info['columns'])
            
            return schema_info, column_text
            
        except Exception as e:
            logger.error(f"Error reading schema from {file_path}: {e}")
            raise

    def transfer_schema_to_redhot(self, file_path: str):
        """Transfer schema information from a parquet file to red-hot memory."""
        try:
            # Get schema information and text for embedding
            schema_info, column_text = self.get_schema_info(file_path)
            
            # Create embedding from column names
            embedding = self.model.encode([column_text])[0]
            
            # Add to red-hot memory
            self.red_hot.add_vector(embedding, metadata=schema_info)
            
            logger.debug(f"Transferred schema for {file_path}")
            
        except Exception as e:
            logger.error(f"Error transferring schema for {file_path}: {e}")
            raise

    def transfer_all_schemas(self):
        """Transfer schema information from cold storage metadata to red-hot memory."""
        print("\nStarting schema transfer process...")
        
        # Get all schemas from cold storage
        print("Fetching schemas from cold storage...")
        schemas = self.cold.get_all_schemas()
        total_schemas = len(schemas)
        
        print(f"\nFound {total_schemas} schemas to process")
        
        stats = {
            'total_files': total_schemas,
            'processed_files': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'by_source_type': {
                'base': 0,
                'divisions': 0,
                'transportation': 0,
                'buildings': 0,
                'unknown': 0
            }
        }
        
        print("\nProcessing schemas:")
        for schema in schemas:
            try:
                # Create embeddings for each column name individually
                columns = schema.get('columns', [])
                file_path = schema.get('file_path', '')
                dtypes = schema.get('dtypes', {})
                
                # Determine geometry column
                geom_col = None
                for possible_name in ['geom', 'geometry', 'c', 'the_geom']:
                    if possible_name in columns:
                        geom_col = possible_name
                        break
                
                for column in columns:
                    # Create embedding for single column name
                    embedding = self.model.encode([column])[0]
                    
                    # Add to red-hot memory with complete metadata
                    self.red_hot.add_vector(
                        embedding,
                        metadata={
                            'file_path': file_path,
                            'column_name': column,
                            'dtype': dtypes.get(column, 'unknown'),
                            'all_columns': columns,  # Include full schema context
                            'geometry_column': geom_col,  # Add geometry column name
                            'type': 'column'
                        }
                    )
                
                stats['processed_files'] += 1
                stats['successful_transfers'] += 1
                
                # Update source type stats
                source_type = 'unknown'
                if 'base' in file_path:
                    source_type = 'base'
                elif 'divisions' in file_path:
                    source_type = 'divisions'
                elif 'transportation' in file_path:
                    source_type = 'transportation'
                elif 'buildings' in file_path:
                    source_type = 'buildings'
                stats['by_source_type'][source_type] += 1
                
                # Print progress every 10 files
                if stats['processed_files'] % 10 == 0:
                    print(f"Progress: {stats['processed_files']}/{total_schemas} schemas processed")
                    print(f"Success: {stats['successful_transfers']}, Failed: {stats['failed_transfers']}")
                    
            except Exception as e:
                logger.error(f"Error transferring schema: {e}")
                stats['failed_transfers'] += 1
                stats['processed_files'] += 1
        
        print("\nTransfer completed!")
        print(f"Total processed: {stats['processed_files']}/{total_schemas}")
        print(f"Successful: {stats['successful_transfers']}")
        print(f"Failed: {stats['failed_transfers']}")
        
        print("\nBy source type:")
        for source_type, count in stats['by_source_type'].items():
            if count > 0:
                print(f"  {source_type}: {count} schemas")
        
        # Print final FAISS index info
        print(f"\nFinal FAISS index size: {self.red_hot.index.ntotal} vectors")
        print(f"FAISS index dimension: {self.red_hot.dimension}")
        print(f"FAISS storage location: {self.faiss_dir}")
        
        return stats

    def show_first_ten(self):
        """Display the first 10 vectors and their metadata from the FAISS index."""
        print("\nRetrieving first 10 vectors from FAISS index:")
        
        if self.red_hot.index.ntotal == 0:
            print("FAISS index is empty!")
            return
        
        # Create a dummy query vector (using the first vector in the index)
        dummy_vector = self.red_hot.index.reconstruct(0)
        
        # Search for nearest neighbors
        D, I = self.red_hot.index.search(dummy_vector.reshape(1, -1), min(10, self.red_hot.index.ntotal))
        
        print(f"\nFound {len(I[0])} vectors:")
        for i, idx in enumerate(I[0]):
            metadata = self.red_hot.get_metadata(int(idx))
            print(f"\nVector {i+1}:")
            print(f"Distance: {D[0][i]:.4f}")
            print(f"File path: {metadata.get('file_path', 'N/A')}")
            print(f"Columns: {', '.join(metadata.get('columns', []))}")
            print("-" * 80)

def main():
    """Main function to run the transfer process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add project root to Python path
    project_root = str(Path(__file__).parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to Python path")
    
    transfer = ColdToRedHot()
    stats = transfer.transfer_all_schemas()
    
    # Print final summary
    print("\nTransfer Summary:")
    print(f"Total schemas: {stats['total_files']}")
    print(f"Successfully transferred: {stats['successful_transfers']}")
    print(f"Failed transfers: {stats['failed_transfers']}")
    print("\nBy source type:")
    for source_type, count in stats['by_source_type'].items():
        if count > 0:  # Only show non-zero counts
            print(f"  {source_type}: {count} schemas")

if __name__ == "__main__":
    main() 