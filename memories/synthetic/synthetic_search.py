#!/usr/bin/env python
"""
Synthetic search layer that enhances FAISS index searching capabilities.
This layer prioritizes search across memory tiers, starting with red_hot,
and provides detailed metadata about search results.
"""

import os
import asyncio
import logging
import json
import sys
import argparse
from typing import Dict, List, Any, Optional, Union, Tuple

from memories.core.memory_index import memory_index
from memories.core.memory_catalog import memory_catalog
# Import memory_retrieval for future compatibility
from memories.core.memory_retrieval import memory_retrieval

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SyntheticSearch:
    """
    Synthetic search layer for enhancing FAISS index searches.
    
    This class adds a synthetic layer between the user query and the raw FAISS search,
    prioritizing search across memory tiers and enhancing the results with metadata
    and query capability information.
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize the synthetic search layer.
        
        Args:
            similarity_threshold: Threshold for considering a match relevant (0-1)
                                  Lower values = more permissive matches
                                  Higher values = stricter matches
                                  Typical range: 0.6-0.8
        """
        self.similarity_threshold = similarity_threshold
        # Convert similarity threshold to distance threshold (assuming cosine distance)
        # Distance = 1 - similarity, so threshold_distance = 1 - similarity_threshold
        self.distance_threshold = 1.0 - similarity_threshold
        
    async def initialize_all_tiers(self):
        """Initialize all memory tiers for searching."""
        # Initialize red_hot tier
        memory_index._init_red_hot()
        # Initialize other tiers as fallbacks
        memory_index._init_hot()
        memory_index._init_warm()
        memory_index._init_cold()
        memory_index._init_glacier()
        
    async def update_tier_index(self, tier: str):
        """
        Update a specific memory tier's index.
        
        Args:
            tier: Memory tier to update ("red_hot", "hot", "warm", "cold", "glacier")
        """
        try:
            await memory_index.update_index(tier)
            if tier in memory_index.indexes:
                logger.info(f"{tier} index updated with {memory_index.indexes[tier].ntotal} vectors")
            else:
                logger.warning(f"{tier} index was not created")
        except Exception as e:
            logger.error(f"Error updating {tier} index: {e}")
            
    async def synthetic_search(self, 
                    query: str, 
                    tiers: List[str] = ["red_hot", "hot", "warm", "cold", "glacier"], 
                    k: int = 5,
                    stop_on_first_match: bool = True
                   ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a synthetic search across memory tiers.
        
        This search adds a synthetic layer that prioritizes tiers and filters by similarity threshold.
        
        Args:
            query: Search query string
            tiers: List of tiers to search, in priority order
            k: Number of results to return per tier
            stop_on_first_match: Whether to stop searching once a match is found
            
        Returns:
            Dictionary with keys for each tier and values containing the search results
        """
        results = {}
        first_match_found = False
        
        for tier in tiers:
            if first_match_found and stop_on_first_match:
                logger.info(f"Skipping tier {tier} as match already found")
                continue
                
            # Update the index for this tier
            await self.update_tier_index(tier)
                
            # Search this tier
            logger.info(f"Searching tier: {tier}")
            try:
                tier_results = await memory_index.search(query, tiers=[tier], k=k)
                
                # Filter results by threshold
                filtered_results = []
                for result in tier_results:
                    # Lower distance = better match
                    if result.get('distance', float('inf')) <= self.distance_threshold:
                        filtered_results.append(result)
                
                if filtered_results:
                    results[tier] = filtered_results
                    first_match_found = True
                    logger.info(f"Found {len(filtered_results)} matches in {tier} tier")
                else:
                    logger.info(f"No matches found in {tier} tier that meet threshold ({self.similarity_threshold})")
            except Exception as e:
                logger.error(f"Error searching {tier} tier: {e}")
        
        return results
    
    async def get_enhanced_metadata(self, search_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Enhance the search results with additional metadata.
        
        Args:
            search_results: Results from the search method
            
        Returns:
            Enhanced metadata dictionary with additional information and query capabilities
        """
        enhanced_results = {}
        
        for tier, results in search_results.items():
            enhanced_results[tier] = []
            
            for result in results:
                enhanced_result = dict(result)  # Copy the original result
                
                # Extract key information
                data_id = result.get('data_id')
                location = result.get('location', '')
                
                # Add database and table info if available
                if '/' in location:
                    db_name, table_name = location.split('/', 1)
                    enhanced_result['database_name'] = db_name
                    enhanced_result['table_name'] = table_name
                
                # Add schema information if available
                if 'schema' in result and result['schema']:
                    schema = result['schema']
                    if 'columns' in schema:
                        enhanced_result['columns'] = schema['columns']
                    if 'type' in schema:
                        enhanced_result['data_structure_type'] = schema['type']
                
                # Try to get additional info from the catalog
                try:
                    if data_id:
                        catalog_info = await memory_catalog.get_data_info(data_id)
                        if catalog_info:
                            enhanced_result['catalog_info'] = catalog_info
                except Exception as e:
                    logger.warning(f"Error getting catalog info for {data_id}: {e}")
                
                # Infer query capabilities
                if 'columns' in enhanced_result:
                    enhanced_result['query_capabilities'] = self._infer_query_capabilities(
                        enhanced_result.get('columns', []),
                        enhanced_result.get('data_structure_type', '')
                    )
                
                enhanced_results[tier].append(enhanced_result)
        
        return enhanced_results
    
    def _infer_query_capabilities(self, columns: List[str], data_type: str) -> Dict[str, Any]:
        """
        Infer the query capabilities based on the columns and data type.
        
        This creates a synthetic layer that enriches the raw FAISS results with
        inferred query capabilities based on column names and data types.
        
        Args:
            columns: List of column names
            data_type: Type of data structure
            
        Returns:
            Dictionary of query capabilities and example queries
        """
        capabilities = {
            "supports_filtering": True,
            "supports_aggregation": True,
            "spatial_query": False,
            "text_search": False,
            "time_series": False,
            "potential_queries": []
        }
        
        # Check for spatial columns
        spatial_columns = [col for col in columns if any(term in col.lower() for term in 
                                                   ['geom', 'geometry', 'point', 'polygon', 'location', 'coordinate', 'lat', 'lon'])]
        if spatial_columns:
            capabilities["spatial_query"] = True
            capabilities["potential_queries"].append({
                "type": "spatial",
                "example": f"SELECT * FROM table WHERE ST_Within(ST_GeomFromWKB({spatial_columns[0]}), ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat))"
            })
        
        # Check for text search columns
        text_columns = [col for col in columns if any(term in col.lower() for term in 
                                                ['name', 'title', 'description', 'text', 'comment'])]
        if text_columns:
            capabilities["text_search"] = True
            capabilities["potential_queries"].append({
                "type": "text_search",
                "example": f"SELECT * FROM table WHERE {text_columns[0]} LIKE '%search_term%'"
            })
        
        # Check for time series data
        time_columns = [col for col in columns if any(term in col.lower() for term in 
                                                ['time', 'date', 'timestamp', 'created', 'updated'])]
        if time_columns:
            capabilities["time_series"] = True
            capabilities["potential_queries"].append({
                "type": "time_series",
                "example": f"SELECT * FROM table WHERE {time_columns[0]} BETWEEN start_date AND end_date"
            })
        
        # Add general filtering example
        if columns:
            capabilities["potential_queries"].append({
                "type": "filtering",
                "example": f"SELECT * FROM table WHERE {columns[0]} = 'value'"
            })
        
        # Add aggregation example
        numeric_columns = [col for col in columns if any(term in col.lower() for term in 
                                                   ['id', 'count', 'amount', 'value', 'number', 'total', 'sum', 'price'])]
        if numeric_columns:
            capabilities["potential_queries"].append({
                "type": "aggregation",
                "example": f"SELECT AVG({numeric_columns[0]}) FROM table GROUP BY {columns[0] if columns else 'column'}"
            })
        
        return capabilities


async def main():
    """Process command line arguments and run the search."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Synthetic Search Layer for FAISS indexes')
    parser.add_argument('query', nargs='?', default="building", help='Search query term')
    parser.add_argument('--threshold', '-t', type=float, default=0.7, 
                        help='Similarity threshold (0-1, lower is more permissive)')
    parser.add_argument('--all-tiers', '-a', action='store_true', 
                        help='Search all tiers even after a match is found')
    parser.add_argument('--max-results', '-k', type=int, default=5,
                        help='Maximum results per tier')
    parser.add_argument('--tiers', type=str, default="red_hot,hot,warm,cold,glacier",
                        help='Comma-separated list of tiers to search')
    
    args = parser.parse_args()
    
    # Create search instance
    search = SyntheticSearch(similarity_threshold=args.threshold)
    
    # Initialize memory tiers
    await search.initialize_all_tiers()
    
    # Split tiers string into list
    tiers_list = args.tiers.split(',')
    
    # Perform the search
    print(f"Running synthetic search for: '{args.query}' with threshold {args.threshold}")
    print(f"Searching tiers (in order): {', '.join(tiers_list)}")
    
    results = await search.synthetic_search(
        query=args.query,
        tiers=tiers_list,
        k=args.max_results,
        stop_on_first_match=not args.all_tiers
    )
    
    if not results:
        print(f"No results found for '{args.query}' that meet the similarity threshold.")
        return
    
    # Get enhanced metadata
    enhanced_results = await search.get_enhanced_metadata(results)
    
    # Print the results
    print(f"\n===== SYNTHETIC SEARCH RESULTS FOR: '{args.query}' =====\n")
    
    for tier, tier_results in enhanced_results.items():
        print(f"{tier.upper()} TIER: {len(tier_results)} results")
        
        for i, result in enumerate(tier_results):
            print(f"\nResult {i+1}:")
            print(f"  Data ID: {result.get('data_id', 'N/A')}")
            
            # Database and table info
            if 'database_name' in result:
                print(f"  Database: {result['database_name']}")
            if 'table_name' in result:
                print(f"  Table: {result['table_name']}")
            
            print(f"  Distance: {result.get('distance', 'N/A')}")
            print(f"  Location: {result.get('location', 'N/A')}")
            
            # Display columns
            if 'columns' in result:
                cols = result['columns']
                print(f"  Columns: {', '.join(str(col) for col in cols[:10])}{'...' if len(cols) > 10 else ''}")
            
            # Display query capabilities
            if 'query_capabilities' in result:
                caps = result['query_capabilities']
                print("\n  Query Capabilities:")
                
                if caps.get('spatial_query'):
                    print("  ✓ Supports spatial queries")
                if caps.get('text_search'):
                    print("  ✓ Supports text search")
                if caps.get('time_series'):
                    print("  ✓ Supports time series analysis")
                
                print("\n  Potential Query Examples:")
                for query_example in caps.get('potential_queries', [])[:3]:
                    print(f"  - {query_example['type'].title()}: {query_example['example']}")
            
            print("\n" + "-"*50)


# Create a singleton instance for easier importing
synthetic_search = SyntheticSearch()


if __name__ == "__main__":
    asyncio.run(main()) 