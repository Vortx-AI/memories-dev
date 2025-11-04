"""
Standard design patterns for memories-dev.
Provides thread-safe and robust implementations of common patterns.
"""

import threading
from typing import Any, Type, TypeVar, Generic, Optional, Dict
from abc import ABC, abstractmethod
import weakref
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ThreadSafeSingleton(type, Generic[T]):
    """Thread-safe singleton metaclass.
    
    This metaclass ensures that only one instance of a class exists
    per process, with proper thread safety and cleanup handling.
    """
    
    _instances: Dict[Type, Any] = {}
    _locks: Dict[Type, threading.Lock] = {}
    _cleanup_registered = False
    
    def __call__(cls, *args, **kwargs):
        """Create or return existing instance."""
        # Get or create lock for this class
        if cls not in cls._locks:
            cls._locks[cls] = threading.Lock()
        
        # Double-checked locking pattern
        if cls not in cls._instances:
            with cls._locks[cls]:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
                    
                    # Register cleanup handler
                    if not cls._cleanup_registered:
                        import atexit
                        atexit.register(cls._cleanup_instances)
                        cls._cleanup_registered = True
                    
                    logger.debug(f"Created singleton instance of {cls.__name__}")
        
        return cls._instances[cls]
    
    @classmethod
    def _cleanup_instances(cls):
        """Clean up all singleton instances."""
        for instance_cls, instance in cls._instances.items():
            try:
                if hasattr(instance, 'cleanup'):
                    instance.cleanup()
                elif hasattr(instance, 'close'):
                    instance.close()
                logger.debug(f"Cleaned up singleton instance of {instance_cls.__name__}")
            except Exception as e:
                logger.error(f"Error cleaning up {instance_cls.__name__}: {e}")
        
        cls._instances.clear()
        cls._locks.clear()
    
    @classmethod
    def reset_instance(cls, instance_cls: Type):
        """Reset a specific singleton instance (useful for testing)."""
        if instance_cls in cls._instances:
            with cls._locks.get(instance_cls, threading.Lock()):
                if instance_cls in cls._instances:
                    try:
                        instance = cls._instances[instance_cls]
                        if hasattr(instance, 'cleanup'):
                            instance.cleanup()
                    except Exception as e:
                        logger.error(f"Error during reset cleanup: {e}")
                    finally:
                        del cls._instances[instance_cls]

class Singleton(ABC, metaclass=ThreadSafeSingleton):
    """Base class for singleton objects.
    
    Provides a standard interface for singleton classes with
    proper initialization and cleanup handling.
    """
    
    def __init__(self):
        """Initialize the singleton instance."""
        self._initialized = False
        self._lock = threading.RLock()
        self._initialize()
    
    def _initialize(self):
        """Initialize the singleton (called once per instance)."""
        with self._lock:
            if not self._initialized:
                self.initialize()
                self._initialized = True
    
    @abstractmethod
    def initialize(self):
        """Override this method to implement singleton initialization."""
        pass
    
    def cleanup(self):
        """Override this method to implement cleanup logic."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if the singleton is initialized."""
        return self._initialized

class WeakSingleton(type):
    """Weak reference singleton metaclass.
    
    Allows garbage collection of singleton instances when no strong
    references remain, useful for resource management.
    """
    
    _instances: Dict[Type, weakref.ref] = {}
    _locks: Dict[Type, threading.Lock] = {}
    
    def __call__(cls, *args, **kwargs):
        """Create or return existing weak instance."""
        if cls not in cls._locks:
            cls._locks[cls] = threading.Lock()
        
        with cls._locks[cls]:
            # Check if we have a valid weak reference
            if cls in cls._instances:
                instance = cls._instances[cls]()
                if instance is not None:
                    return instance
            
            # Create new instance
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = weakref.ref(instance, cls._cleanup_ref)
            logger.debug(f"Created weak singleton instance of {cls.__name__}")
            return instance
    
    @classmethod
    def _cleanup_ref(cls, ref):
        """Clean up dead weak reference."""
        # Find and remove the dead reference
        for instance_cls, weak_ref in list(cls._instances.items()):
            if weak_ref is ref:
                del cls._instances[instance_cls]
                logger.debug(f"Cleaned up weak reference for {instance_cls.__name__}")
                break

class FactorySingleton(ThreadSafeSingleton):
    """Factory singleton that can create different instances based on parameters.
    
    Useful for configuration managers or connection pools that need
    different instances based on configuration.
    """
    
    _factory_instances: Dict[tuple, Any] = {}
    
    def __call__(cls, *args, **kwargs):
        """Create or return instance based on factory key."""
        # Create factory key from args and kwargs
        factory_key = (cls, args, tuple(sorted(kwargs.items())))
        
        if cls not in cls._locks:
            cls._locks[cls] = threading.Lock()
        
        with cls._locks[cls]:
            if factory_key not in cls._factory_instances:
                instance = super(ThreadSafeSingleton, cls).__call__(*args, **kwargs)
                cls._factory_instances[factory_key] = instance
                logger.debug(f"Created factory singleton instance of {cls.__name__} with key {factory_key}")
            
            return cls._factory_instances[factory_key]

class SingletonRegistry:
    """Registry for managing singleton instances globally."""
    
    _registry: Dict[str, Any] = {}
    _lock = threading.Lock()
    
    @classmethod
    def register(cls, name: str, instance: Any, override: bool = False):
        """Register a singleton instance by name.
        
        Args:
            name: Name to register instance under
            instance: Instance to register
            override: Whether to override existing registration
        """
        with cls._lock:
            if name in cls._registry and not override:
                raise ValueError(f"Singleton '{name}' already registered")
            
            cls._registry[name] = instance
            logger.debug(f"Registered singleton '{name}'")
    
    @classmethod
    def get(cls, name: str, default: Any = None) -> Any:
        """Get a registered singleton by name.
        
        Args:
            name: Name of singleton to retrieve
            default: Default value if not found
            
        Returns:
            Singleton instance or default
        """
        with cls._lock:
            return cls._registry.get(name, default)
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a singleton by name.
        
        Args:
            name: Name of singleton to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        with cls._lock:
            if name in cls._registry:
                instance = cls._registry.pop(name)
                if hasattr(instance, 'cleanup'):
                    try:
                        instance.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up {name}: {e}")
                logger.debug(f"Unregistered singleton '{name}'")
                return True
            return False
    
    @classmethod
    def clear(cls):
        """Clear all registered singletons."""
        with cls._lock:
            for name, instance in cls._registry.items():
                if hasattr(instance, 'cleanup'):
                    try:
                        instance.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up {name}: {e}")
            
            cls._registry.clear()
            logger.debug("Cleared all registered singletons")
    
    @classmethod
    def list_registered(cls) -> list:
        """List all registered singleton names."""
        with cls._lock:
            return list(cls._registry.keys())

# Decorator for easy singleton creation
def singleton(cls):
    """Decorator to make a class a singleton.
    
    Usage:
        @singleton
        class MyClass:
            pass
    """
    # Add ThreadSafeSingleton as metaclass
    if not hasattr(cls, '__metaclass__'):
        class SingletonClass(cls, metaclass=ThreadSafeSingleton):
            pass
        SingletonClass.__name__ = cls.__name__
        SingletonClass.__qualname__ = cls.__qualname__
        return SingletonClass
    else:
        raise ValueError("Class already has a metaclass")

# Example usage and testing utilities
class SingletonTester:
    """Utility class for testing singleton implementations."""
    
    @staticmethod
    def test_singleton_behavior(singleton_class: Type, *args, **kwargs):
        """Test that a class properly implements singleton behavior.
        
        Args:
            singleton_class: Class to test
            *args, **kwargs: Arguments to pass to constructor
            
        Returns:
            True if singleton behavior is correct
        """
        # Test that multiple instantiations return the same object
        instance1 = singleton_class(*args, **kwargs)
        instance2 = singleton_class(*args, **kwargs)
        
        if instance1 is not instance2:
            raise AssertionError("Singleton class returned different instances")
        
        # Test thread safety
        import concurrent.futures
        
        def create_instance():
            return singleton_class(*args, **kwargs)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_instance) for _ in range(10)]
            instances = [future.result() for future in futures]
        
        # All instances should be the same object
        if not all(instance is instance1 for instance in instances):
            raise AssertionError("Singleton not thread-safe")
        
        logger.info(f"Singleton test passed for {singleton_class.__name__}")
        return True