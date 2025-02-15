from typing import Dict, Any
import logging
from memories.utils.query.location_extractor import LocationExtractor

class QueryContext:
    def __init__(self):
        """Initialize QueryContext with LocationExtractor"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.location_extractor = LocationExtractor()

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query through LocationExtractor
        
        Args:
            query (str): User query
            
        Returns:
            Dict[str, Any]: Location extraction results
        """
        try:
            self.logger.info(f"Processing query through LocationExtractor: {query}")
            return self.location_extractor.process(query)
            
        except Exception as e:
            self.logger.error(f"Error in QueryContext: {str(e)}")
            return {
                "error": str(e),
                "query": query
            }
            
        