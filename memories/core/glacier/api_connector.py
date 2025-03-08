"""Base API connector for glacier data sources."""

from typing import Dict, Any, Optional
import aiohttp
import logging
from .base import GlacierConnector

class APIConnector(GlacierConnector):
    """Base class for API-based glacier connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the API connector.
        
        Args:
            config: Configuration dictionary containing:
                - base_url: Base URL for API requests
                - timeout: Request timeout in seconds
                - headers: Optional request headers
        """
        super().__init__(config)
        self.base_url = config['base_url']
        self.timeout = config.get('timeout', 30)
        self.headers = config.get('headers', {})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make an HTTP request to the API.
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Optional[Dict[str, Any]]: Response data or None on error
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(
                            f"API request failed: {response.status} - {await response.text()}"
                        )
                        return None
        except Exception as e:
            self.logger.error(f"Request error: {str(e)}")
            return None
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate API query parameters.
        
        Args:
            query: Query parameters to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return bool(query)
    
    async def retrieve(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from the API source.
        
        Args:
            query: Query parameters
            
        Returns:
            Optional[Dict[str, Any]]: Retrieved data or None if not found
        """
        raise NotImplementedError("Subclasses must implement retrieve()") 