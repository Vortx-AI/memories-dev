"""Memory store functionality for storing data in different memory tiers."""

import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import sys
import os
import asyncio

from memories.core.memory_manager import MemoryManager
from memories.core.memory_catalog import memory_catalog
from memories.core.warm import WarmMemory

logger = logging.getLogger(__name__)

class MemoryStore:
    """Memory store for handling data storage across different memory tiers."""
    
    def __init__(self):
        """Initialize memory store."""
        self.memory_manager = MemoryManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize memory tiers as None - will be created on demand
        self._hot_memory = None
        self._warm_memory = None
        self._cold_memory = None
        self._red_hot_memory = None

    def _init_hot(self) -> None:
        """Initialize hot memory on demand."""
        if not self._hot_memory:
            from memories.core.hot import HotMemory
            self._hot_memory = HotMemory()

    def _init_warm(self) -> None:
        """Initialize warm memory on demand."""
        if not self._warm_memory:
            self._warm_memory = WarmMemory()

    def _init_cold(self) -> None:
        """Initialize cold memory on demand."""
        if not self._cold_memory:
            from memories.core.cold import ColdMemory
            self._cold_memory = ColdMemory()

    def _init_red_hot(self) -> None:
        """Initialize red hot memory on demand."""
        if not self._red_hot_memory:
            from memories.core.red_hot import RedHotMemory
            self._red_hot_memory = RedHotMemory()

    def _get_data_size(self, data: Any) -> int:
        """Get size of data in bytes."""
        try:
            if hasattr(data, 'memory_usage'):
                # For pandas DataFrame
                return data.memory_usage(deep=True).sum()
            elif hasattr(data, 'nbytes'):
                # For numpy arrays
                return data.nbytes
            else:
                # For other objects, use sys.getsizeof
                return sys.getsizeof(data)
        except Exception as e:
            self.logger.warning(f"Could not determine data size: {e}")
            return 0

    def _get_data_type(self, data: Any) -> str:
        """Get type of data as string."""
        if hasattr(data, 'dtypes'):
            return 'dataframe'
        elif hasattr(data, 'dtype'):
            return 'array'
        else:
            return data.__class__.__name__.lower()

    async def store(
        self,
        to_tier: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Store data in specified memory tier.
        
        Args:
            to_tier: Memory tier to store in ("glacier", "cold", "warm", "hot", "red_hot")
            data: Data to store
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            
        Returns:
            bool: True if storage was successful, False otherwise
            
        Raises:
            ValueError: If the tier is invalid
        """
        valid_tiers = ["glacier", "cold", "warm", "hot", "red_hot"]
        if to_tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {to_tier}. Must be one of {valid_tiers}")

        try:
            # Get data size and type
            size = self._get_data_size(data)
            data_type = self._get_data_type(data)
            
            # Store data in the specified tier
            success = False
            location = None
            
            if to_tier == "glacier":
                success = await self._store_in_glacier(data, metadata=metadata, tags=tags)
                location = f"glacier/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif to_tier == "cold":
                self._init_cold()
                success = await self._cold_memory.store(data, metadata=metadata, tags=tags)
                location = f"cold/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif to_tier == "warm":
                self._init_warm()
                result = await self._warm_memory.store(data, metadata=metadata, tags=tags)
                
                if result["success"]:
                    # Use the table name as the location
                    location = result["table_name"]
                    data_id = result["data_id"]
                    success = True
                else:
                    success = False
                    location = None
            elif to_tier == "hot":
                self._init_hot()
                success = await self._hot_memory.store(data, metadata=metadata, tags=tags)
                location = f"hot/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif to_tier == "red_hot":
                self._init_red_hot()
                success = await self._red_hot_memory.store(data, metadata=metadata, tags=tags)
                location = str(self._red_hot_memory.storage_path / f"red_hot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

            # Register in catalog if storage was successful
            if success and location:
                try:
                    # For warm memory, use the table_name parameter
                    if to_tier == "warm" and 'data_id' in locals():
                        await memory_catalog.register_data(
                            tier=to_tier,
                            location=location,
                            size=size,
                            data_type=data_type,
                            tags=tags,
                            metadata=metadata,
                            table_name=location  # Use the table name as both location and table_name
                        )
                    else:
                        await memory_catalog.register_data(
                            tier=to_tier,
                            location=location,
                            size=size,
                            data_type=data_type,
                            tags=tags,
                            metadata=metadata
                        )
                except Exception as e:
                    self.logger.error(f"Failed to register in catalog: {e}")
                    # Don't fail the operation if catalog registration fails
                    pass

            return success

        except Exception as e:
            self.logger.error(f"Error storing in {to_tier} tier: {e}")
            return False

    async def _store_in_glacier(
        self,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store data in glacier storage."""
        # Placeholder for glacier storage implementation
        self.logger.info("Glacier storage not implemented yet")
        return False

    def cleanup(self) -> None:
        """Clean up resources for all memory tiers."""
        try:
            if self._hot_memory:
                self._hot_memory.cleanup()
            if self._warm_memory:
                self._warm_memory.cleanup()
            if self._cold_memory:
                self._cold_memory.cleanup()
            if self._red_hot_memory:
                self._red_hot_memory.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup is performed."""
        self.cleanup()

    async def retrieve_from_warm(
        self,
        table_name: str,
        db_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from a specific table in warm memory.
        
        Args:
            table_name: Name of the table to retrieve data from
            db_name: Optional name of the database file (without .duckdb extension)
            
        Returns:
            Retrieved data or None if not found
        """
        try:
            self._init_warm()
            return await self._warm_memory.retrieve(table_name=table_name, db_name=db_name)
        except Exception as e:
            self.logger.error(f"Error retrieving from warm memory table {table_name}: {e}")
            return None

    async def import_parquet_to_warm(
        self,
        parquet_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> bool:
        """
        Import data from a parquet file into warm memory.
        
        Args:
            parquet_file: Path to the parquet file
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            table_name: Optional name for the table to create. If None, a name will be generated.
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            self._init_warm()
            
            # Get data size for catalog
            size = os.path.getsize(parquet_file)
            data_type = "parquet"
            
            # Import the parquet file
            result = await self._warm_memory.import_from_parquet(
                parquet_file=parquet_file,
                metadata=metadata,
                tags=tags,
                db_name=db_name,
                table_name=table_name
            )
            
            if result["success"]:
                # Register in catalog
                try:
                    await memory_catalog.register_data(
                        tier="warm",
                        location=result["table_name"],
                        size=size,
                        data_type=data_type,
                        tags=tags,
                        metadata=metadata,
                        table_name=result["table_name"]
                    )
                except Exception as e:
                    self.logger.error(f"Failed to register parquet import in catalog: {e}")
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error importing parquet to warm memory: {e}")
            return False
    
    async def import_duckdb_to_warm(
        self,
        source_db_file: str,
        tables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None
    ) -> bool:
        """
        Import tables from another DuckDB database into warm memory.
        
        Args:
            source_db_file: Path to the source DuckDB database file
            tables: Optional list of table names to import. If None, imports all tables.
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            self._init_warm()
            
            # Get data size for catalog
            size = os.path.getsize(source_db_file)
            data_type = "duckdb"
            
            # Import from the DuckDB file
            result = await self._warm_memory.import_from_duckdb(
                source_db_file=source_db_file,
                tables=tables,
                metadata=metadata,
                tags=tags,
                db_name=db_name
            )
            
            if result["success"]:
                # Register each imported table in catalog
                for table_name, data_id in result["data_ids"].items():
                    try:
                        await memory_catalog.register_data(
                            tier="warm",
                            location=table_name,
                            size=size // len(result["imported_tables"]),  # Approximate size per table
                            data_type=data_type,
                            tags=tags,
                            metadata=metadata,
                            table_name=table_name
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to register table {table_name} in catalog: {e}")
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error importing DuckDB to warm memory: {e}")
            return False

    async def import_csv_to_warm(
        self,
        csv_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> bool:
        """
        Import data from a CSV file into warm memory.
        
        Args:
            csv_file: Path to the CSV file
            metadata: Optional metadata about the data
            tags: Optional tags for categorizing the data
            db_name: Optional name of the database file to store in (without .duckdb extension)
            table_name: Optional name for the table to create. If None, a name will be generated.
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            self._init_warm()
            
            # Get data size for catalog
            size = os.path.getsize(csv_file)
            data_type = "csv"
            
            # Import the CSV file
            result = await self._warm_memory.import_from_csv(
                csv_file=csv_file,
                metadata=metadata,
                tags=tags,
                db_name=db_name,
                table_name=table_name
            )
            
            if result["success"]:
                # Register in catalog
                try:
                    await memory_catalog.register_data(
                        tier="warm",
                        location=result["table_name"],
                        size=size,
                        data_type=data_type,
                        tags=tags,
                        metadata=metadata,
                        table_name=result["table_name"]
                    )
                except Exception as e:
                    self.logger.error(f"Failed to register CSV import in catalog: {e}")
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error importing CSV to warm memory: {e}")
            return False

async def main():
    """Main function to demonstrate importing tables from DuckDB to warm memory."""
    try:
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        
        # Source database path
        source_db = ""
        
        # Check if source database exists
        if not os.path.exists(source_db):
            logger.error(f"Source database not found: {source_db}")
            return
            
        # Define metadata and tags
        metadata = {
           
        }
        
        
        # Import tables using memory_store
        logger.info(f"Starting import from {source_db}")
        
        # Use the default configuration from memory manager
        success = await memory_store.import_duckdb_to_warm(
            source_db_file=source_db,
            metadata=metadata,
            #tags=tags
            # No db_name specified - will use default from config
        )
        
        if success:
            logger.info("Import completed successfully!")
            
            # List all tables in the catalog
            logger.info("Checking memory catalog entries...")
            catalog_entries = await memory_catalog.get_tier_data("warm")
            
            if catalog_entries:
                logger.info(f"Found {len(catalog_entries)} entries in memory catalog:")
                for entry in catalog_entries:
                    logger.info(f"- Table: {entry['table_name']}")
                    logger.info(f"  Location: {entry['location']}")
                    logger.info(f"  Tags: {entry['tags']}")
                    logger.info(f"  Created: {entry['created_at']}")
                    logger.info("---")
            else:
                logger.warning("No entries found in memory catalog")
        else:
            logger.error("Import failed")
            
    except Exception as e:
        logger.exception(f"Error in main function: {e}")

if __name__ == "__main__":
    asyncio.run(main())

# Create singleton instance
memory_store = MemoryStore()
