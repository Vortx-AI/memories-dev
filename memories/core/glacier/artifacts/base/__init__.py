"""
Mock glacier artifacts base module for documentation build.

This module provides mock objects for the memories.core.glacier.artifacts.base module
to allow documentation to be built without requiring all dependencies.
"""

class Artifact:
    """Base class for glacier artifacts."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the artifact."""
        pass
    
    def store(self, *args, **kwargs):
        """Store the artifact in glacier storage."""
        pass
    
    def retrieve(self, *args, **kwargs):
        """Retrieve the artifact from glacier storage."""
        pass 