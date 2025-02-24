from typing import Dict, Any
import logging
from memories.utils.query.location_extractor import LocationExtractor
from memories.agents import BaseAgent

class QueryContext(BaseAgent):
    """Agent specialized in processing query context."""
    
    def __init__(self, memory_store: Any = None):
        """Initialize QueryContext with LocationExtractor"""
        super().__init__(memory_store=memory_store, name="query_context_agent")
        self.location_extractor = LocationExtractor()

    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process data using this agent.
        
        This method implements the required abstract method from BaseAgent.
        It serves as a wrapper around process_query.
        
        Args:
            query: String containing the user's query
            
        Returns:
            Dict[str, Any]: Processing results
        """
        query = kwargs.get('query', args[0] if args else None)
        
        if not query:
            return {
                "status": "error",
                "error": "No query provided",
                "data": None
            }
            
        try:
            result = self.process_query(query)
            return {
                "status": "success" if "error" not in result else "error",
                "data": result if "error" not in result else None,
                "error": result.get("error")
            }
        except Exception as e:
            self.logger.error(f"Error in process: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }

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
            
    def requires_model(self) -> bool:
        """This agent does not require a model."""
        return False
            
        