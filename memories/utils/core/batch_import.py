"""
Batch import utilities for memory management.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from memories.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

def batch_import_parquet(
    memory_manager: MemoryManager,
    folder_path: Union[str, Path],
    theme: Optional[str] = None,
    tag: Optional[str] = None,
    recursive: bool = True,
    pattern: str = "*.parquet"
) -> Dict[str, Any]:
    """
    Import all Parquet files from a folder into cold memory.
    
    Args:
        memory_manager: Initialized MemoryManager instance
        folder_path: Path to folder containing Parquet files
        theme: Optional theme for organizing data (e.g., 'buildings')
        tag: Optional tag for organizing data (e.g., 'commercial')
        recursive: Whether to search recursively in subfolders
        pattern: File pattern to match (default: "*.parquet")
        
    Returns:
        Dict containing:
            success_count: Number of files successfully imported
            failed_count: Number of files that failed to import
            failed_files: List of files that failed to import
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")
        
    # Find all Parquet files
    if recursive:
        parquet_files = list(folder_path.rglob(pattern))
    else:
        parquet_files = list(folder_path.glob(pattern))
        
    if not parquet_files:
        logger.warning(f"No Parquet files found in {folder_path}")
        return {
            "success_count": 0,
            "failed_count": 0,
            "failed_files": []
        }
    
    # Track results
    success_count = 0
    failed_files = []
    
    # Process each file
    for file_path in parquet_files:
        try:
            logger.info(f"Importing {file_path}")
            
            # Add file to cold memory
            success = memory_manager.add_to_tier(
                tier='cold',
                data=str(file_path),
                metadata={
                    'source_path': str(file_path),
                    'theme': theme,
                    'tag': tag,
                    'file_size': file_path.stat().st_size,
                    'imported_from': 'batch_import'
                }
            )
            
            if success:
                success_count += 1
            else:
                failed_files.append(str(file_path))
                
        except Exception as e:
            logger.error(f"Error importing {file_path}: {e}")
            failed_files.append(str(file_path))
    
    results = {
        "success_count": success_count,
        "failed_count": len(failed_files),
        "failed_files": failed_files
    }
    
    logger.info(f"Import complete: {results}")
    return results 