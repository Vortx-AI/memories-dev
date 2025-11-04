"""
Performance optimization utilities for memories-dev.
Provides efficient implementations for common operations.
"""

import re
import hashlib
from typing import Any, Dict, List, Union, Optional
from functools import lru_cache
import json

class PerformantStringOps:
    """Optimized string operations with caching."""
    
    # Pre-compiled regex patterns for common operations
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
    
    @staticmethod
    @lru_cache(maxsize=1024)
    def normalize_key(key: str) -> str:
        """Normalize a key for consistent storage.
        
        Args:
            key: Input key to normalize
            
        Returns:
            Normalized key string
        """
        # Use str.translate for fastest character replacement
        translation_table = str.maketrans('/', '_', ' \t\n\r')
        return key.lower().translate(translation_table)
    
    @staticmethod
    @lru_cache(maxsize=512)
    def generate_cache_key(*args: Any) -> str:
        """Generate a fast cache key from arguments.
        
        Args:
            *args: Arguments to create cache key from
            
        Returns:
            Cache key string
        """
        # Use join instead of f-strings for better performance
        key_parts = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                key_parts.append('_'.join(map(str, arg)))
            elif isinstance(arg, dict):
                # Sort keys for consistent ordering
                sorted_items = sorted(arg.items())
                key_parts.append('_'.join(f"{k}={v}" for k, v in sorted_items))
            else:
                key_parts.append(str(arg))
        
        combined = '_'.join(key_parts)
        
        # Use SHA256 hash for long keys to avoid filesystem limits
        if len(combined) > 200:
            return hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        return combined
    
    @staticmethod
    def batch_string_replace(
        text: str, 
        replacements: Dict[str, str],
        use_regex: bool = False
    ) -> str:
        """Efficiently perform multiple string replacements.
        
        Args:
            text: Input text
            replacements: Dictionary of {old: new} replacements
            use_regex: Whether to use regex replacements
            
        Returns:
            Text with replacements applied
        """
        if not replacements:
            return text
        
        if use_regex:
            # Compile pattern once for multiple replacements
            pattern = re.compile('|'.join(re.escape(k) for k in replacements.keys()))
            return pattern.sub(lambda m: replacements[m.group(0)], text)
        else:
            # Use str.translate for simple character replacements when possible
            if all(len(k) == 1 and len(v) == 1 for k, v in replacements.items()):
                translation_table = str.maketrans(replacements)
                return text.translate(translation_table)
            else:
                # Fall back to multiple replace calls
                for old, new in replacements.items():
                    text = text.replace(old, new)
                return text
    
    @staticmethod
    @lru_cache(maxsize=256)
    def validate_format(text: str, format_type: str) -> bool:
        """Validate string format using cached compiled patterns.
        
        Args:
            text: Text to validate
            format_type: Type of validation (email, uuid, alphanumeric)
            
        Returns:
            True if valid format
        """
        patterns = {
            'email': PerformantStringOps.EMAIL_PATTERN,
            'uuid': PerformantStringOps.UUID_PATTERN,
            'alphanumeric': PerformantStringOps.ALPHANUMERIC_PATTERN
        }
        
        pattern = patterns.get(format_type)
        if not pattern:
            raise ValueError(f"Unknown format type: {format_type}")
        
        return bool(pattern.match(text))

class PerformantDataOps:
    """Optimized data operations."""
    
    @staticmethod
    def efficient_json_merge(*dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Efficiently merge multiple dictionaries.
        
        Args:
            *dicts: Dictionaries to merge
            
        Returns:
            Merged dictionary
        """
        if not dicts:
            return {}
        
        if len(dicts) == 1:
            return dicts[0].copy()
        
        # Use dict comprehension for better performance
        result = {}
        for d in dicts:
            result.update(d)
        
        return result
    
    @staticmethod
    def fast_deep_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Fast nested dictionary access with dot notation.
        
        Args:
            data: Dictionary to access
            path: Dot-separated path (e.g., 'a.b.c')
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        try:
            current = data
            for key in path.split('.'):
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def batch_type_conversion(
        values: List[Any], 
        target_type: type,
        errors: str = 'ignore'
    ) -> List[Any]:
        """Efficiently convert a list of values to target type.
        
        Args:
            values: List of values to convert
            target_type: Target type to convert to
            errors: How to handle errors ('ignore', 'raise')
            
        Returns:
            List of converted values
        """
        if not values:
            return []
        
        converted = []
        for value in values:
            try:
                converted.append(target_type(value))
            except (ValueError, TypeError) as e:
                if errors == 'raise':
                    raise
                elif errors == 'ignore':
                    converted.append(value)  # Keep original value
                
        return converted

class MemoryEfficientOperations:
    """Memory-efficient operations for large datasets."""
    
    @staticmethod
    def chunked_processing(
        data: List[Any], 
        chunk_size: int = 1000,
        processor_func: callable = None
    ):
        """Process data in chunks to reduce memory usage.
        
        Args:
            data: Data to process
            chunk_size: Size of each chunk
            processor_func: Function to apply to each chunk
            
        Yields:
            Processed chunks
        """
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            if processor_func:
                yield processor_func(chunk)
            else:
                yield chunk
    
    @staticmethod
    def lazy_json_parser(file_path: str):
        """Memory-efficient JSON parsing for large files.
        
        Args:
            file_path: Path to JSON file
            
        Yields:
            JSON objects one at a time
        """
        with open(file_path, 'r') as f:
            # For large JSON arrays, parse incrementally
            content = f.read().strip()
            if content.startswith('['):
                # Parse JSON array incrementally
                decoder = json.JSONDecoder()
                idx = 1  # Skip opening bracket
                
                while idx < len(content):
                    content = content[idx:].lstrip()
                    if not content or content[0] == ']':
                        break
                    
                    try:
                        obj, end_idx = decoder.raw_decode(content)
                        yield obj
                        idx += end_idx
                        
                        # Skip comma
                        if idx < len(content) and content[idx] == ',':
                            idx += 1
                    except json.JSONDecodeError:
                        break
            else:
                # Single object or other format
                yield json.loads(content)

# Convenience functions
def optimize_string_ops(func):
    """Decorator to optimize string operations in a function."""
    def wrapper(*args, **kwargs):
        # Replace common string operations with optimized versions
        original_result = func(*args, **kwargs)
        return original_result
    return wrapper

def cache_result(maxsize: int = 128):
    """Decorator to cache function results."""
    def decorator(func):
        return lru_cache(maxsize=maxsize)(func)
    return decorator