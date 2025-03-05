#!/usr/bin/env python3
"""
Script to build and maintain the spatial index for geospatial data.
"""

import logging
import argparse
from pathlib import Path
from memories.core.memory_retrieval import SpatialIndexBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Build and maintain spatial index for geospatial data.')
    parser.add_argument('--data-dir', type=str, help='Path to data directory (optional)')
    parser.add_argument('--force-rebuild', action='store_true', help='Force rebuild of index for all files')
    parser.add_argument('--stats-only', action='store_true', help='Only show index statistics without building')
    args = parser.parse_args()

    try:
        # Initialize the spatial index builder
        builder = SpatialIndexBuilder(data_dir=args.data_dir)
        
        if args.stats_only:
            # Just show current index statistics
            logger.info("\nCurrent Index Statistics:")
            stats = builder.get_index_stats()
            
            if stats:
                logger.info(f"Total indexed files: {stats['total_entries']}")
                if 'total_bounds' in stats:
                    bounds = stats['total_bounds']
                    logger.info("\nTotal Geographic Bounds:")
                    logger.info(f"  Min Longitude: {bounds['min_lon']}")
                    logger.info(f"  Min Latitude: {bounds['min_lat']}")
                    logger.info(f"  Max Longitude: {bounds['max_lon']}")
                    logger.info(f"  Max Latitude: {bounds['max_lat']}")
                if 'geometry_columns' in stats:
                    logger.info("\nGeometry Columns:")
                    for col, count in stats['geometry_columns'].items():
                        logger.info(f"  {col}: {count} files")
            else:
                logger.warning("No index statistics available")
        else:
            # Build or update the index
            logger.info("Starting spatial index build...")
            builder.build_index(force_rebuild=args.force_rebuild)
            
            # Show updated statistics
            logger.info("\nUpdated Index Statistics:")
            stats = builder.get_index_stats()
            if stats:
                logger.info(f"Total indexed files: {stats['total_entries']}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        builder.cleanup()
    
    return 0

if __name__ == '__main__':
    exit(main()) 