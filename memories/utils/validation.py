"""
Comprehensive input validation framework for memories-dev.
Provides security and data integrity validation for all inputs.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from datetime import datetime, date
from pathlib import Path
import json
from functools import wraps

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class Validator:
    """Base validator class with common validation methods."""
    
    @staticmethod
    def validate_string(
        value: Any, 
        min_length: int = 0, 
        max_length: int = 10000,
        pattern: Optional[str] = None,
        allowed_chars: Optional[str] = None,
        forbidden_chars: Optional[str] = None,
        strip_whitespace: bool = True
    ) -> str:
        """Validate and sanitize string input.
        
        Args:
            value: Input value to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            pattern: Regex pattern that must match
            allowed_chars: Set of allowed characters
            forbidden_chars: Set of forbidden characters
            strip_whitespace: Whether to strip leading/trailing whitespace
            
        Returns:
            Validated and sanitized string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            if value is None:
                raise ValidationError("String value cannot be None")
            try:
                value = str(value)
            except Exception as e:
                raise ValidationError(f"Cannot convert value to string: {e}")
        
        if strip_whitespace:
            value = value.strip()
        
        # Length validation
        if len(value) < min_length:
            raise ValidationError(f"String too short. Minimum length: {min_length}")
        if len(value) > max_length:
            raise ValidationError(f"String too long. Maximum length: {max_length}")
        
        # Pattern validation
        if pattern and not re.match(pattern, value):
            raise ValidationError(f"String does not match required pattern: {pattern}")
        
        # Character validation
        if allowed_chars:
            invalid_chars = set(value) - set(allowed_chars)
            if invalid_chars:
                raise ValidationError(f"String contains forbidden characters: {invalid_chars}")
        
        if forbidden_chars:
            found_chars = set(value) & set(forbidden_chars)
            if found_chars:
                raise ValidationError(f"String contains forbidden characters: {found_chars}")
        
        return value
    
    @staticmethod
    def validate_number(
        value: Any,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        integer_only: bool = False
    ) -> Union[int, float]:
        """Validate numeric input.
        
        Args:
            value: Input value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            integer_only: Whether to allow only integers
            
        Returns:
            Validated number
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError("Numeric value cannot be None")
        
        try:
            if integer_only:
                if isinstance(value, float) and not value.is_integer():
                    raise ValidationError("Value must be an integer")
                value = int(value)
            else:
                value = float(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid numeric value: {e}")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"Value {value} is below minimum {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"Value {value} is above maximum {max_value}")
        
        return value
    
    @staticmethod
    def validate_coordinates(
        latitude: Any,
        longitude: Any
    ) -> Tuple[float, float]:
        """Validate geographic coordinates.
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            Tuple of validated (lat, lon) coordinates
            
        Raises:
            ValidationError: If coordinates are invalid
        """
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid coordinate values: {e}")
        
        if not (-90 <= lat <= 90):
            raise ValidationError(f"Invalid latitude: {lat}. Must be between -90 and 90")
        
        if not (-180 <= lon <= 180):
            raise ValidationError(f"Invalid longitude: {lon}. Must be between -180 and 180")
        
        return lat, lon
    
    @staticmethod
    def validate_bbox(
        bbox: Any
    ) -> Tuple[float, float, float, float]:
        """Validate bounding box coordinates.
        
        Args:
            bbox: Bounding box as [min_lon, min_lat, max_lon, max_lat] or dict
            
        Returns:
            Tuple of validated bbox coordinates
            
        Raises:
            ValidationError: If bbox is invalid
        """
        if isinstance(bbox, dict):
            try:
                bbox = [bbox['west'], bbox['south'], bbox['east'], bbox['north']]
            except KeyError as e:
                raise ValidationError(f"Missing bbox coordinate: {e}")
        
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValidationError("Bounding box must have 4 coordinates")
        
        try:
            min_lon, min_lat, max_lon, max_lat = map(float, bbox)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid bbox coordinates: {e}")
        
        # Validate individual coordinates
        Validator.validate_coordinates(min_lat, min_lon)
        Validator.validate_coordinates(max_lat, max_lon)
        
        # Validate bbox logic
        if min_lon >= max_lon:
            raise ValidationError(f"min_lon ({min_lon}) must be less than max_lon ({max_lon})")
        if min_lat >= max_lat:
            raise ValidationError(f"min_lat ({min_lat}) must be less than max_lat ({max_lat})")
        
        return min_lon, min_lat, max_lon, max_lat
    
    @staticmethod
    def validate_file_path(
        path: Any,
        must_exist: bool = False,
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: Optional[float] = None
    ) -> Path:
        """Validate file path.
        
        Args:
            path: File path to validate
            must_exist: Whether file must exist
            allowed_extensions: List of allowed file extensions
            max_size_mb: Maximum file size in MB
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If path is invalid
        """
        if not isinstance(path, (str, Path)):
            raise ValidationError("Path must be string or Path object")
        
        try:
            path = Path(path).resolve()
        except Exception as e:
            raise ValidationError(f"Invalid path: {e}")
        
        # Security check - prevent path traversal
        if ".." in str(path):
            raise ValidationError("Path traversal not allowed")
        
        if must_exist and not path.exists():
            raise ValidationError(f"File does not exist: {path}")
        
        if path.exists() and path.is_file():
            # Extension validation
            if allowed_extensions:
                if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                    raise ValidationError(f"File extension not allowed. Allowed: {allowed_extensions}")
            
            # Size validation
            if max_size_mb:
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb > max_size_mb:
                    raise ValidationError(f"File too large: {size_mb:.1f}MB > {max_size_mb}MB")
        
        return path
    
    @staticmethod
    def validate_datetime(
        value: Any,
        format_string: Optional[str] = None
    ) -> datetime:
        """Validate datetime input.
        
        Args:
            value: Datetime value to validate
            format_string: Expected datetime format
            
        Returns:
            Validated datetime object
            
        Raises:
            ValidationError: If datetime is invalid
        """
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        
        if isinstance(value, str):
            if format_string:
                try:
                    return datetime.strptime(value, format_string)
                except ValueError as e:
                    raise ValidationError(f"Invalid datetime format: {e}")
            else:
                # Try common ISO formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                
                raise ValidationError(f"Cannot parse datetime: {value}")
        
        raise ValidationError(f"Invalid datetime type: {type(value)}")
    
    @staticmethod
    def validate_json(
        value: Any,
        max_depth: int = 10,
        max_keys: int = 1000
    ) -> Dict[str, Any]:
        """Validate JSON input.
        
        Args:
            value: JSON value to validate
            max_depth: Maximum nesting depth
            max_keys: Maximum number of keys
            
        Returns:
            Validated JSON object
            
        Raises:
            ValidationError: If JSON is invalid
        """
        if isinstance(value, dict):
            json_obj = value
        elif isinstance(value, str):
            try:
                json_obj = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        else:
            raise ValidationError(f"Invalid JSON type: {type(value)}")
        
        def count_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise ValidationError(f"JSON too deep. Maximum depth: {max_depth}")
            
            if isinstance(obj, dict):
                for value in obj.values():
                    count_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    count_depth(item, current_depth + 1)
        
        def count_keys(obj):
            count = 0
            if isinstance(obj, dict):
                count += len(obj)
                for value in obj.values():
                    count += count_keys(value)
            elif isinstance(obj, list):
                for item in obj:
                    count += count_keys(item)
            return count
        
        # Validate structure
        count_depth(json_obj)
        
        key_count = count_keys(json_obj)
        if key_count > max_keys:
            raise ValidationError(f"Too many JSON keys: {key_count} > {max_keys}")
        
        return json_obj

def validate_input(**validators):
    """Decorator for input validation.
    
    Args:
        **validators: Mapping of parameter names to validation functions
        
    Example:
        @validate_input(
            name=lambda x: Validator.validate_string(x, min_length=1, max_length=100),
            age=lambda x: Validator.validate_number(x, min_value=0, max_value=150, integer_only=True)
        )
        def create_user(name: str, age: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each parameter
            for param_name, validator_func in validators.items():
                if param_name in bound_args.arguments:
                    try:
                        validated_value = validator_func(bound_args.arguments[param_name])
                        bound_args.arguments[param_name] = validated_value
                    except ValidationError as e:
                        logger.error(f"Validation error for parameter '{param_name}': {e}")
                        raise ValidationError(f"Invalid {param_name}: {e}")
            
            return func(*bound_args.args, **bound_args.kwargs)
        return wrapper
    return decorator

# Common validation patterns
def validate_user_input(value: str) -> str:
    """Validate general user input."""
    return Validator.validate_string(
        value,
        max_length=1000,
        forbidden_chars=['<', '>', '"', "'", '&', '\x00'],
        strip_whitespace=True
    )

def validate_sql_safe(value: str) -> str:
    """Validate string to be SQL injection safe."""
    dangerous_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(--|/\*|\*/)',
        r'(\'|"|\;)',
        r'(\bUNION\b|\bOR\b\s+\d+\s*=\s*\d+)',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError("Input contains potentially dangerous SQL patterns")
    
    return Validator.validate_string(value, max_length=1000)

def validate_memory_key(key: str) -> str:
    """Validate memory storage key."""
    return Validator.validate_string(
        key,
        min_length=1,
        max_length=255,
        pattern=r'^[a-zA-Z0-9_\-\.]+$'
    )