#!/usr/bin/env python
"""
Memory query layer that enhances FAISS index searching capabilities.
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
from memories.core.memory_retrieval import memory_retrieval

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryQuery:
    """
    Memory query layer for enhancing FAISS index searches.
    
    This class adds a query layer between the user query and the raw FAISS search,
    prioritizing search across memory tiers and enhancing the results with metadata
    and query capability information.
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize the memory query layer.
        
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
            
    async def search(self, 
                    query: str, 
                    tiers: List[str] = ["red_hot", "hot", "warm", "cold", "glacier"], 
                    k: int = 5,
                    stop_on_first_match: bool = True
                   ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a search across memory tiers.
        
        This search adds a query layer that prioritizes tiers and filters by similarity threshold.
        
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
        
        This creates a query layer that enriches the raw FAISS results with
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
                "example": f"SELECT AVG({numeric_columns[0]}) FROM table GROUP BY category"
            })
        
        return capabilities

async def main():
    """Run a test search."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test memory query functionality')
    parser.add_argument('query', help='Search query string')
    parser.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold (0-1)')
    parser.add_argument('--k', type=int, default=5, help='Number of results per tier')
    args = parser.parse_args()
    
    # Initialize memory query
    memory_query = MemoryQuery(similarity_threshold=args.threshold)
    
    # Initialize all tiers
    await memory_query.initialize_all_tiers()
    
    # Perform search
    results = await memory_query.search(args.query, k=args.k)
    
    # Get enhanced metadata
    enhanced_results = await memory_query.get_enhanced_metadata(results)
    
    # Print results
    print(json.dumps(enhanced_results, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 