#!/usr/bin/env python
"""
Script for moving data between memory tiers.

This script demonstrates using the MemoryTiering class to move data between
different memory tiers, particularly from Glacier to Cold storage.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).absolute().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"Added {project_root} to Python path")

# Load environment variables
load_dotenv()

from memories.core.memory_tiering import MemoryTiering

async def tier_data(source_tier: str, target_tier: str, data_key: str, new_key: str = None):
    """Move data from one memory tier to another.
    
    Args:
        source_tier: Source tier ('glacier', 'cold', 'warm', 'hot')
        target_tier: Target tier ('cold', 'warm', 'hot', 'red_hot')
        data_key: Key identifying the data in the source tier
        new_key: Optional new key to use in the target tier
    """
    tiering = MemoryTiering()
    
    print(f"Moving data with key '{data_key}' from {source_tier} to {target_tier}...")
    
    # For Glacier to Cold specifically
    if source_tier == 'glacier' and target_tier == 'cold':
        print(f"Retrieving from Glacier key: {data_key}")
        success = await tiering.glacier_to_cold(data_key, new_key)
    else:
        # Use the generic method for other tier combinations
        success = await tiering.promote_to_tier(data_key, source_tier, target_tier, new_key)
    
    if success:
        print(f"Successfully moved data from {source_tier} to {target_tier}")
        if new_key:
            print(f"New data key in {target_tier} tier: {new_key}")
        else:
            print(f"Using the same key in {target_tier} tier: {data_key}")
    else:
        print(f"Failed to move data from {source_tier} to {target_tier}")

def main():
    """Parse command-line arguments and execute the appropriate action."""
    parser = argparse.ArgumentParser(description='Move data between memory tiers')
    parser.add_argument('source_tier', choices=['glacier', 'cold', 'warm', 'hot'],
                        help='Source memory tier')
    parser.add_argument('target_tier', choices=['cold', 'warm', 'hot', 'red_hot'],
                        help='Target memory tier')
    parser.add_argument('data_key', help='Key identifying the data in the source tier')
    parser.add_argument('--new-key', '-n', help='New key to use in the target tier (optional)')
    
    args = parser.parse_args()
    
    # Validate the tiering direction
    valid_tiers = ['glacier', 'cold', 'warm', 'hot', 'red_hot']
    source_index = valid_tiers.index(args.source_tier)
    target_index = valid_tiers.index(args.target_tier)
    
    if target_index <= source_index:
        print(f"Error: Target tier '{args.target_tier}' is not warmer than source tier '{args.source_tier}'")
        print("Data can only be moved from colder tiers to warmer tiers")
        return
        
    # Run the async function
    asyncio.run(tier_data(args.source_tier, args.target_tier, args.data_key, args.new_key))

if __name__ == "__main__":
    main() 