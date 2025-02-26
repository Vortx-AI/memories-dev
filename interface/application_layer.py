"""
Application Layer Interface
This module implements the highest level (Layer 7) of the OSI model for the Earth Memory Layer system.
It provides user-facing interfaces and high-level APIs.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ApplicationResponse:
    """Standard response format for application layer operations"""
    success: bool
    data: Any
    message: str
    status_code: int

class ApplicationInterface(ABC):
    """Base interface for all application layer components"""
    
    @abstractmethod
    async def initialize(self) -> ApplicationResponse:
        """Initialize the interface"""
        pass
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> ApplicationResponse:
        """Process incoming requests"""
        pass
    
    @abstractmethod
    async def handle_response(self, response: ApplicationResponse) -> None:
        """Handle outgoing responses"""
        pass

class UserInterface(ApplicationInterface):
    """Handles user interactions and input/output operations"""
    
    async def initialize(self) -> ApplicationResponse:
        try:
            # Initialize user interface components
            return ApplicationResponse(
                success=True,
                data=None,
                message="User interface initialized successfully",
                status_code=200
            )
        except Exception as e:
            return ApplicationResponse(
                success=False,
                data=None,
                message=f"Failed to initialize user interface: {str(e)}",
                status_code=500
            )
    
    async def process_request(self, request: Dict[str, Any]) -> ApplicationResponse:
        # Process user requests
        return ApplicationResponse(
            success=True,
            data=request,
            message="Request processed successfully",
            status_code=200
        )
    
    async def handle_response(self, response: ApplicationResponse) -> None:
        # Handle and format responses for user presentation
        pass

class APIGateway(ApplicationInterface):
    """Handles external API communications"""
    
    async def initialize(self) -> ApplicationResponse:
        try:
            # Initialize API gateway
            return ApplicationResponse(
                success=True,
                data=None,
                message="API gateway initialized successfully",
                status_code=200
            )
        except Exception as e:
            return ApplicationResponse(
                success=False,
                data=None,
                message=f"Failed to initialize API gateway: {str(e)}",
                status_code=500
            )
    
    async def process_request(self, request: Dict[str, Any]) -> ApplicationResponse:
        # Process API requests
        return ApplicationResponse(
            success=True,
            data=request,
            message="API request processed successfully",
            status_code=200
        )
    
    async def handle_response(self, response: ApplicationResponse) -> None:
        # Handle API responses
        pass

class ApplicationLayer:
    """Main Application Layer controller"""
    
    def __init__(self):
        self.user_interface = UserInterface()
        self.api_gateway = APIGateway()
        self.interfaces: Dict[str, ApplicationInterface] = {
            'user': self.user_interface,
            'api': self.api_gateway
        }
    
    async def initialize_all(self) -> Dict[str, ApplicationResponse]:
        """Initialize all application layer interfaces"""
        results = {}
        for name, interface in self.interfaces.items():
            results[name] = await interface.initialize()
        return results
    
    async def process_request(self, interface_name: str, request: Dict[str, Any]) -> ApplicationResponse:
        """Process a request through the specified interface"""
        if interface_name not in self.interfaces:
            return ApplicationResponse(
                success=False,
                data=None,
                message=f"Interface {interface_name} not found",
                status_code=404
            )
        return await self.interfaces[interface_name].process_request(request) 