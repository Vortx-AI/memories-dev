#!/usr/bin/env python3

import asyncio
import logging
from memories.core.memory_catalog import memory_catalog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_catalog():
    """Check what's registered in the memory catalog."""
    try:
        # Query the catalog for all warm tier data
        results = await memory_catalog.get_tier_data("warm")
        
        if not results:
            print("No entries found in memory catalog for warm tier")
            return
            
        print(f"\nFound {len(results)} entries in memory catalog (warm tier):")
        print("=" * 80)
        
        for entry in results:
            print(f"\nData ID: {entry['data_id']}")
            print("-" * 80)
            print(f"Location (table): {entry['location']}")
            print(f"Table name: {entry['table_name']}")
            print(f"Created at: {entry['created_at']}")
            print(f"Last accessed: {entry['last_accessed']}")
            print(f"Access count: {entry['access_count']}")
            print(f"Size: {entry['size']} bytes")
            print(f"Data type: {entry['data_type']}")
            print(f"Tags: {entry['tags']}")
            print(f"Additional metadata: {entry['additional_meta']}")
            print()

    except Exception as e:
        logger.error(f"Error checking catalog: {e}")

if __name__ == "__main__":
    asyncio.run(check_catalog()) 